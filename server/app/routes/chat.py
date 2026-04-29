import time
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models import ChatRequest, ChatResponse, SafetyInfo, MetaInfo, SourceItem
from app.services import safety_service, gemini_service, rag_service
from app.services.source_router import classify_intent
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("chat_route")

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

# Intents that are handled by safety_service but should also carry intent metadata
_SAFETY_REFUSAL_INTENTS = {"political_persuasion", "illegal_voting"}

# Intents whose direct_response bypasses RAG and Gemini entirely
_DIRECT_ANSWER_INTENTS = {
    "greeting",
    "assistant_identity",
    "current_date_time",
    "unclear_followup",
    "current_election_info",
}


def _build_rag_fallback(message: str, persona: str, fallback_reason: str) -> ChatResponse:
    """Return a best-effort answer from local RAG when Gemini is unavailable."""
    chunks = rag_service.retrieve(message, top_k=3)
    if chunks:
        context_text = "\n\n".join(
            f"**{c['heading']}**\n{c['content']}" for c in chunks
        )
        answer = (
            f"_The AI model is temporarily unavailable ({fallback_reason}), "
            f"so I'm answering from the built-in VoteWise knowledge base._\n\n"
            f"{context_text}\n\n"
            "Always verify from **eci.gov.in** or **voters.eci.gov.in**."
        )
        sources = []
        seen = set()
        for c in chunks:
            if c["source_url"] not in seen:
                sources.append(SourceItem(title=c["source_title"], url=c["source_url"], type=c["source_type"]))
                seen.add(c["source_url"])
    else:
        answer = (
            f"_The AI model is temporarily unavailable ({fallback_reason}). "
            "Please visit **eci.gov.in** or **voters.eci.gov.in** for official information._"
        )
        sources = [SourceItem(title="Election Commission of India", url="https://eci.gov.in", type="official")]

    return ChatResponse(
        answer=answer,
        sources=sources,
        safety=SafetyInfo(blocked=False, reason=None),
        meta=MetaInfo(
            model="rag-only",
            used_rag=True,
            used_search_grounding=False,
            intent="civic_static",
            used_direct_answer=False,
            used_model=False,
        )
    )


@router.post("/api/chat", response_model=ChatResponse)
@limiter.limit("30/minute")  # Generous for dev/demo; tighten in production
async def chat(request: Request, body: ChatRequest):
    server_req_id = str(uuid.uuid4())[:8]
    client_req_id = request.headers.get("X-Client-Request-Id", "none")
    t_start = time.monotonic()

    logger.info(
        f"POST /api/chat START | server_req={server_req_id} | client_req={client_req_id} "
        f"| ip={request.client.host} | persona={body.persona} | msgLen={len(body.message)}"
    )

    # ── 1. Safety pre-screen (no Gemini call) ───────────────────────────────
    logger.info(f"[{server_req_id}] Safety check START")
    safety_check = safety_service.check_message(body.message)
    if not safety_check["safe"]:
        elapsed = round((time.monotonic() - t_start) * 1000)
        logger.info(f"[{server_req_id}] Safety BLOCKED | geminiCalled=False | durationMs={elapsed}")
        return ChatResponse(
            answer=safety_check["response"],
            sources=[],
            safety=SafetyInfo(blocked=True, reason=safety_check["reason"]),
            meta=MetaInfo(
                model="safety",
                used_rag=False,
                used_search_grounding=False,
                intent="political_persuasion_or_illegal",
                used_direct_answer=True,
                used_model=False,
            )
        )
    logger.info(f"[{server_req_id}] Safety check PASSED")

    # ── 2. Intent classification ─────────────────────────────────────────────
    intent_result = classify_intent(body.message, context=body.context)
    intent = intent_result["intent"]
    direct_response = intent_result.get("direct_response")
    use_rag = intent_result.get("use_rag", True)
    use_model = intent_result.get("use_model", True)

    logger.info(f"[{server_req_id}] Intent: {intent} | direct={direct_response is not None} | use_rag={use_rag} | use_model={use_model}")

    # ── 3. Direct-answer short-circuit (no RAG / no Gemini) ─────────────────
    if direct_response is not None:
        elapsed = round((time.monotonic() - t_start) * 1000)
        logger.info(f"[{server_req_id}] Direct answer returned | intent={intent} | durationMs={elapsed}")
        return ChatResponse(
            answer=direct_response,
            sources=[],
            safety=SafetyInfo(blocked=False, reason=None),
            meta=MetaInfo(
                model="direct",
                used_rag=False,
                used_search_grounding=False,
                intent=intent,
                used_direct_answer=True,
                used_model=False,
            )
        )

    # ── 4. RAG + Gemini flow (civic_static / political_party_neutral / unclear_followup with context / current_election_info / current_party_info / current_public_info) ──
    try:
        logger.info(f"[{server_req_id}] Calling gemini_service | intent={intent}")
        response = await gemini_service.generate_chat_response(
            message=body.message,
            persona=body.persona,
            context=body.context,
            intent=intent,
            use_rag=use_rag,
        )
        elapsed = round((time.monotonic() - t_start) * 1000)
        logger.info(f"[{server_req_id}] POST /api/chat SUCCESS | durationMs={elapsed} | blocked={response.safety.blocked}")

        # Patch meta with intent fields (gemini_service sets its own model/used_rag)
        response.meta.intent = intent
        response.meta.used_direct_answer = False
        response.meta.used_model = True
        
        # Override model name if grounding was used
        if response.meta.used_search_grounding:
            response.meta.model = "gemini-grounded"
            
        return response

    except (ValueError, PermissionError) as e:
        # Config / auth errors — not recoverable via RAG fallback
        elapsed = round((time.monotonic() - t_start) * 1000)
        logger.error(f"[{server_req_id}] Config/auth error | durationMs={elapsed} | msg={str(e)}")
        return JSONResponse(status_code=503, content={"error": str(e)})

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        # Gemini quota / overload / timeout — use RAG fallback instead of error
        elapsed = round((time.monotonic() - t_start) * 1000)
        err_str = str(e)
        fallback_reason = (
            "gemini_quota" if "quota" in err_str.lower() or "rate" in err_str.lower()
            else "gemini_timeout" if "timeout" in err_str.lower()
            else "gemini_unavailable"
        )
        logger.warning(
            f"[{server_req_id}] Gemini unavailable — using RAG fallback "
            f"| reason={fallback_reason} | durationMs={elapsed} | err={err_str[:80]}"
        )
        fallback = _build_rag_fallback(body.message, body.persona, fallback_reason)
        fallback.meta.intent = intent
        return fallback
