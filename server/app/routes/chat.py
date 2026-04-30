import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models import ChatRequest, ChatResponse, SafetyInfo, MetaInfo, SourceItem
from app.services import safety_service, gemini_service, rag_service
from app.services.source_router import (
    classify_intent,
    CURRENT_ELECTION_FALLBACK,
    CURRENT_PARTY_FALLBACK,
    CURRENT_PUBLIC_FALLBACK,
)
from app.prompts.system_prompt import normalize_persona
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("chat_route")

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

# Intents that are handled by safety_service but should also carry intent metadata
_SAFETY_REFUSAL_INTENTS = {"political_persuasion", "illegal_voting"}

# Live intents that must route to Gemini grounding when grounding is enabled.
# These MUST NOT short-circuit to direct fallback if ENABLE_GOOGLE_SEARCH_GROUNDING=true.
_LIVE_INTENTS = {
    "current_public_info",
    "current_election_info",
    "current_party_info",
}

# Fallback text per live intent (used when Gemini fails and no direct_response is available)
_LIVE_INTENT_FALLBACK = {
    "current_election_info": CURRENT_ELECTION_FALLBACK,
    "current_party_info":   CURRENT_PARTY_FALLBACK,
    "current_public_info":  CURRENT_PUBLIC_FALLBACK,
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
            persona_used="general",  # patched by caller
        )
    )


@router.post("/api/chat", response_model=ChatResponse)
@limiter.limit("30/minute")  # Generous for dev/demo; tighten in production
async def chat(request: Request, body: ChatRequest):
    server_req_id = str(uuid.uuid4())[:8]
    client_req_id = request.headers.get("X-Client-Request-Id", "none")
    t_start = time.monotonic()

    # ── Persona normalisation ────────────────────────────────────────────────
    raw_persona = body.persona
    persona = normalize_persona(raw_persona)
    logger.info(
        f"POST /api/chat START | server_req={server_req_id} | client_req={client_req_id} "
        f"| ip={request.client.host} | persona_received={raw_persona!r} "
        f"| persona_normalized={persona!r} | msgLen={len(body.message)}"
    )

    # ── 1. Safety pre-screen (no Gemini call) ───────────────────────────────
    logger.info(f"[{server_req_id}] Safety check START | persona={persona}")
    safety_check = safety_service.check_message(body.message, persona=persona)
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
                persona_used=persona,
            )
        )
    logger.info(f"[{server_req_id}] Safety check PASSED")

    # ── 2. Intent classification ─────────────────────────────────────────────
    intent_result = classify_intent(body.message, context=body.context, persona=persona)
    intent = intent_result["intent"]
    direct_response = intent_result.get("direct_response")
    use_rag = intent_result.get("use_rag", True)
    use_model = intent_result.get("use_model", True)
    logger.info(f"[{server_req_id}] Persona instruction applied | persona={persona} | intent={intent}")

    is_live_intent = intent in _LIVE_INTENTS
    grounding_enabled = settings.ENABLE_GOOGLE_SEARCH_GROUNDING

    # ── DEBUG (server-side only, never exposed to frontend) ──────────────────
    logger.debug(f"[DBG][{server_req_id}] intent={intent}")
    logger.debug(f"[DBG][{server_req_id}] direct_response present={direct_response is not None}")
    logger.debug(f"[DBG][{server_req_id}] grounding enabled={grounding_enabled}")
    logger.info(f"[{server_req_id}] Intent: {intent} | direct={direct_response is not None} | use_rag={use_rag} | use_model={use_model} | is_live={is_live_intent} | grounding={grounding_enabled}")

    # ── 3. Direct-answer short-circuit (no RAG / no Gemini) ─────────────────
    # Live intents with grounding enabled MUST NOT short-circuit here.
    # They must continue to the Gemini grounding branch below.
    # When grounding is enabled, source_router already returns direct_response=None
    # for live intents, so this guard is defence-in-depth.
    skip_direct = is_live_intent and grounding_enabled

    if direct_response is not None and not skip_direct:
        elapsed = round((time.monotonic() - t_start) * 1000)

        checked_at = None
        source_type = None
        if is_live_intent:
            # grounding_enabled is False here (otherwise skip_direct would be True)
            checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            source_type = "unverified_fallback"

        logger.info(
            f"[{server_req_id}] Direct answer returned | intent={intent} "
            f"| is_live={is_live_intent} | grounding_enabled={grounding_enabled} "
            f"| skip_direct={skip_direct} | durationMs={elapsed}"
        )
        logger.debug(f"[DBG][{server_req_id}] skipped fallback because grounding enabled=False")
        logger.debug(f"[DBG][{server_req_id}] gemini_service called=False")

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
                persona_used=persona,
                checkedAt=checked_at,
                sourceType=source_type
            )
        )
    elif direct_response is not None and skip_direct:
        logger.info(f"[{server_req_id}] Skipping direct fallback because grounding is ENABLED | intent={intent}")
        logger.debug(f"[DBG][{server_req_id}] skipped fallback because grounding enabled=True")

    # ── 4. RAG + Gemini flow ─────────────────────────────────────────────────
    # Handles: civic_static, political_party_neutral, unclear_followup (with context),
    # current_election_info, current_party_info, current_public_info (when grounding enabled)
    logger.debug(f"[DBG][{server_req_id}] gemini_service called=True")
    try:
        logger.info(f"[{server_req_id}] Calling gemini_service | intent={intent} | use_rag={use_rag} | grounding_enabled={grounding_enabled}")
        response = await gemini_service.generate_chat_response(
            message=body.message,
            persona=body.persona,
            context=body.context,
            intent=intent,
            use_rag=use_rag,
        )
        elapsed = round((time.monotonic() - t_start) * 1000)

        # ── DEBUG: log grounding metadata outcome ────────────────────────────
        grounding_meta_present = (
            response.meta.used_search_grounding and
            response.meta.sourceType is not None
        )
        source_urls = [s.url for s in response.sources] if response.sources else []
        logger.debug(f"[DBG][{server_req_id}] grounding metadata present={grounding_meta_present}")
        logger.debug(f"[DBG][{server_req_id}] extracted source urls={source_urls}")
        logger.debug(f"[DBG][{server_req_id}] final sourceType={response.meta.sourceType}")
        logger.info(
            f"[{server_req_id}] POST /api/chat SUCCESS | durationMs={elapsed} "
            f"| blocked={response.safety.blocked} | used_search={response.meta.used_search_grounding} "
            f"| sourceType={response.meta.sourceType}"
        )

        # Patch meta with intent and persona fields (gemini_service sets its own model/used_rag)
        response.meta.intent = intent
        response.meta.used_direct_answer = False
        response.meta.used_model = True
        response.meta.persona_used = persona

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
        # Gemini quota / overload / timeout
        elapsed = round((time.monotonic() - t_start) * 1000)
        err_str = str(e)
        fallback_reason = (
            "gemini_quota" if "quota" in err_str.lower() or "rate" in err_str.lower()
            else "gemini_timeout" if "timeout" in err_str.lower()
            else "gemini_unavailable"
        )

        # For live intents: RAG is unsafe/inaccurate for live data.
        # Use the known safe fallback text for this intent.
        # NOTE: when grounding is enabled, direct_response is None (source_router returns None
        # so routing continues to Gemini). We must look up the fallback text directly.
        if is_live_intent:
            # Resolve the safe fallback text: prefer direct_response if set,
            # otherwise use the pre-defined per-intent fallback string.
            safe_fallback_text = direct_response or _LIVE_INTENT_FALLBACK.get(
                intent,
                "I could not verify this from an official source right now. "
                "Please check [eci.gov.in](https://eci.gov.in) for official information."
            )
            checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            logger.warning(
                f"[{server_req_id}] Gemini unavailable — LIVE INTENT safe fallback "
                f"| intent={intent} | reason={fallback_reason} | durationMs={elapsed}"
            )
            logger.debug(f"[DBG][{server_req_id}] final sourceType=unverified_fallback (gemini failed)")
            return ChatResponse(
                answer=safe_fallback_text,
                # sources=[] for unverified_fallback: no source has been validated.
                # ECI is NOT the correct source for general public office queries (current PM, CM, etc).
                # The answer text already embeds appropriate official links per intent.
                sources=[],
                safety=SafetyInfo(blocked=False, reason=None),
                meta=MetaInfo(
                    model="gemini-failed-fallback",
                    used_rag=False,
                    used_search_grounding=grounding_enabled,  # grounding was attempted
                    intent=intent,
                    used_direct_answer=False,
                    used_model=True,  # Gemini was called (but failed)
                    persona_used=persona,
                    checkedAt=checked_at,
                    sourceType="unverified_fallback"
                )
            )

        # Standard RAG fallback for civic/static questions
        logger.warning(
            f"[{server_req_id}] Gemini unavailable — using RAG fallback "
            f"| reason={fallback_reason} | durationMs={elapsed} | err={err_str[:80]}"
        )
        fallback = _build_rag_fallback(body.message, body.persona, fallback_reason)
        fallback.meta.intent = intent
        fallback.meta.persona_used = persona
        return fallback
