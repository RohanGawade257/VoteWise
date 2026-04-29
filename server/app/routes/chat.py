import time
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models import ChatRequest, ChatResponse, SafetyInfo, MetaInfo, SourceItem
from app.services import safety_service, gemini_service, rag_service
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("chat_route")

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

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
        meta=MetaInfo(model="rag-only", used_rag=True, used_search_grounding=False)
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

    # --- Safety pre-screen (no Gemini call) ---
    logger.info(f"[{server_req_id}] Safety check START")
    safety_check = safety_service.check_message(body.message)
    if not safety_check["safe"]:
        elapsed = round((time.monotonic() - t_start) * 1000)
        logger.info(f"[{server_req_id}] Safety BLOCKED | geminiCalled=False | durationMs={elapsed}")
        return ChatResponse(
            answer=safety_check["response"],
            sources=[],
            safety=SafetyInfo(blocked=True, reason=safety_check["reason"]),
            meta=MetaInfo(model=settings.GEMINI_MODEL, used_rag=False, used_search_grounding=False)
        )
    logger.info(f"[{server_req_id}] Safety check PASSED")

    # --- Call Gemini service ---
    try:
        logger.info(f"[{server_req_id}] Calling gemini_service")
        response = await gemini_service.generate_chat_response(
            message=body.message,
            persona=body.persona,
            context=body.context,
            use_current_info=body.use_current_info,
        )
        elapsed = round((time.monotonic() - t_start) * 1000)
        logger.info(f"[{server_req_id}] POST /api/chat SUCCESS | durationMs={elapsed} | blocked={response.safety.blocked}")
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
        return fallback
