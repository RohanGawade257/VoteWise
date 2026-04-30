import re
import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models import ChatRequest, ChatResponse, SafetyInfo, MetaInfo, SourceItem, GuidedFlowInput
from app.services import guided_flow_service
from app.services import safety_service, gemini_service, rag_service
from app.services.source_router import (
    classify_intent,
    CURRENT_ELECTION_FALLBACK,
    CURRENT_PARTY_FALLBACK,
    CURRENT_PUBLIC_FALLBACK,
)
from app.services.tone_service import normalize_persona
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("chat_route")

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

# Rate limit string is loaded from env via settings (default: 30/minute)
_CHAT_RATE_LIMIT = settings.CHAT_RATE_LIMIT

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


# ---------------------------------------------------------------------------
# Guided flow response builder
# ---------------------------------------------------------------------------

def _build_guided_response(result: dict, persona: str) -> ChatResponse:
    """
    Convert a guided_flow_service result dict into a proper ChatResponse.
    All non-guided meta fields are set to safe neutral defaults.
    """
    return ChatResponse(
        answer=result["answer"],
        sources=[
            SourceItem(
                title="Voter Registration Portal",
                url="https://voters.eci.gov.in",
                type="official"
            ),
            SourceItem(
                title="Election Commission of India",
                url="https://eci.gov.in",
                type="official"
            ),
        ],
        safety=SafetyInfo(blocked=False, reason=None),
        meta=MetaInfo(
            model="guided-flow",
            used_rag=False,
            used_search_grounding=False,
            intent="first_time_voter_guided",
            contextual_followup_intent=result.get("contextual_followup_intent"),
            used_direct_answer=True,
            used_model=False,
            persona_used=persona,
            guided_flow_active=True,
            guided_flow_step=result.get("guided_flow_step"),
            guided_flow_state=result.get("guided_flow_state", {}),
            suggested_replies=result.get("suggested_replies", []),
        )
    )


# ---------------------------------------------------------------------------
# Intent detection helpers for fallback answer quality
# ---------------------------------------------------------------------------

# Keywords that strongly signal voter-registration / first-time-voter intent
_REG_SIGNALS = frozenset({
    "18", "first time", "first-time", "firsttime", "new voter",
    "register", "registration", "form 6", "form6", "voter id",
    "voter list", "electoral roll", "enroll", "enrolment",
    "how to vote", "how do i vote", "want to vote",
})

# Headings/content tokens that are IRRELEVANT for registration queries
# — any chunk whose heading contains one of these is penalised
_REG_IRRELEVANT_HEADINGS = frozenset({
    "counting", "vote counting", "count", "result", "results",
    "government formation", "confidence vote", "post-polling",
    "campaign phase", "nomination", "party directory",
})

# EVM / VVPAT signals
_EVM_SIGNALS = frozenset({"evm", "vvpat", "electronic voting", "voting machine", "vvpat slip"})

# NOTA signals
_NOTA_SIGNALS = frozenset({"nota", "none of the above"})

# Coalition / majority signals
_COALITION_SIGNALS = frozenset({
    "coalition", "majority", "government formation",
    "hung parliament", "alliance", "ruling party",
})

# Live / schedule signals — stale RAG is dangerous here
_LIVE_SIGNALS = frozenset({
    "latest", "current", "upcoming", "schedule", "next election",
    "election date", "polling date", "when is", "when are",
})


def _detect_fallback_intent(message: str) -> str:
    """Classify the query into a fallback-answer intent bucket."""
    m = message.lower()
    if any(s in m for s in _REG_SIGNALS):
        return "first_time_voter"
    if any(s in m for s in _EVM_SIGNALS):
        return "evm_vvpat"
    if any(s in m for s in _NOTA_SIGNALS):
        return "nota"
    if any(s in m for s in _COALITION_SIGNALS):
        return "coalition"
    if any(s in m for s in _LIVE_SIGNALS):
        return "live_schedule"
    return "general"


def _is_relevant_chunk(chunk: dict, fallback_intent: str) -> bool:
    """
    Return False if a chunk is clearly irrelevant for the given intent.
    This prevents 'Vote Counting' from appearing in registration answers, etc.
    """
    heading_lower = chunk.get("heading", "").lower()
    file_lower = chunk.get("filename", "").lower()

    if fallback_intent == "first_time_voter":
        # Penalise counting / results / government formation chunks
        if any(kw in heading_lower for kw in _REG_IRRELEVANT_HEADINGS):
            return False
        # Penalise timeline.md chunks that are about post-polling phases
        if "timeline" in file_lower and any(
            kw in heading_lower for kw in {"counting", "post-polling", "government formation", "phase 5", "phase 6"}
        ):
            return False
    return True


def _strip_markdown_artifacts(text: str) -> str:
    """Remove raw markdown artifacts that look ugly in chat bubbles."""
    # Remove leading/trailing underscores used as italic markers
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    # Remove raw horizontal rules
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Remove debug/internal labels
    for label in ("chunk", "score", "gemini_unavailable", "fallback"):
        text = re.sub(rf"\b{label}\b\s*[:=]?\s*", "", text, flags=re.IGNORECASE)
    return text.strip()



def _build_rag_fallback(message: str, persona: str, fallback_reason: str) -> ChatResponse:
    """
    Return a clean, intent-aware answer from the local RAG knowledge base
    when Gemini is unavailable.

    Key improvements over the raw chunk-dump approach:
    - Detects the user's intent from the query
    - For known intents (first-time voter, EVM, NOTA, coalition, live schedule),
      uses a curated template instead of raw chunk text
    - For general civic queries, filters out irrelevant chunks,
      caps at 2 top chunks, and renders a clean bullet-point answer
    - Moves fallback notice entirely into meta.fallback_reason
      so the main answer body is clean and helpful
    """
    fallback_intent = _detect_fallback_intent(message)
    logger.info(f"RAG fallback | fallback_intent={fallback_intent} | reason={fallback_reason}")

    # ── Known-intent: use curated template ──────────────────────────────────
    template_map = {
        "first_time_voter": "fallback_first_time_voter",
        "evm_vvpat":        "fallback_evm_vvpat",
        "nota":             "fallback_nota",
        "coalition":        "fallback_coalition",
        "live_schedule":    "fallback_live_schedule",
    }
    if fallback_intent in template_map:
        from app.services.tone_service import apply_tone_to_template
        template_name = template_map[fallback_intent]
        answer = apply_tone_to_template(template_name, persona)
        # Build source list appropriate for the intent
        if fallback_intent == "first_time_voter":
            sources = [
                SourceItem(title="Voter Registration Portal", url="https://voters.eci.gov.in", type="official"),
                SourceItem(title="Electoral Search", url="https://electoralsearch.eci.gov.in", type="official"),
                SourceItem(title="Election Commission of India", url="https://eci.gov.in", type="official"),
            ]
        else:
            sources = [SourceItem(title="Election Commission of India", url="https://eci.gov.in", type="official")]

        return ChatResponse(
            answer=answer,
            sources=sources,
            safety=SafetyInfo(blocked=False, reason=None),
            meta=MetaInfo(
                model="rag-only",
                used_rag=True,
                used_search_grounding=False,
                intent=fallback_intent,
                used_direct_answer=False,
                used_model=False,
                used_rag_fallback=True,
                fallback_reason=fallback_reason,
                persona_used=persona,
            )
        )

    # ── General civic query: retrieve, filter, and synthesise ───────────────
    raw_chunks = rag_service.retrieve(message, top_k=3)

    # Filter out irrelevant chunks based on intent
    relevant_chunks = [c for c in raw_chunks if _is_relevant_chunk(c, fallback_intent)]

    # Cap at top 2 highly relevant chunks to avoid information overload
    top_chunks = relevant_chunks[:2]

    if top_chunks:
        lines = []
        for c in top_chunks:
            # Clean the chunk content — strip raw markdown artifacts
            content = _strip_markdown_artifacts(c["content"])
            heading = c.get("heading", "")
            if heading:
                lines.append(f"**{heading}**")
            # Convert inline sentences to bullets if they aren't already
            for sentence in content.split(". "):
                sentence = sentence.strip()
                if sentence and not sentence.startswith("-"):
                    lines.append(f"- {sentence}")
                elif sentence:
                    lines.append(sentence)

        body = "\n".join(lines)
        answer = (
            f"{body}\n\n"
            "> Always verify official information at "
            "[eci.gov.in](https://eci.gov.in) or [voters.eci.gov.in](https://voters.eci.gov.in)."
        )

        sources = []
        seen: set = set()
        for c in top_chunks:
            if c["source_url"] not in seen:
                sources.append(SourceItem(
                    title=c["source_title"],
                    url=c["source_url"],
                    type=c["source_type"]
                ))
                seen.add(c["source_url"])
    else:
        # No usable chunks — give a safe, helpful redirect
        from app.services.tone_service import apply_tone_to_template
        answer = apply_tone_to_template("fallback_no_chunks", persona)
        sources = [SourceItem(title="Election Commission of India", url="https://eci.gov.in", type="official")]

    return ChatResponse(
        answer=answer,
        sources=sources,
        safety=SafetyInfo(blocked=False, reason=None),
        meta=MetaInfo(
            model="rag-only",
            used_rag=True,
            used_search_grounding=False,
            intent=fallback_intent,
            used_direct_answer=False,
            used_model=False,
            used_rag_fallback=True,
            fallback_reason=fallback_reason,
            persona_used=persona,
        )
    )



@router.post("/api/chat", response_model=ChatResponse)
@limiter.limit(_CHAT_RATE_LIMIT)
async def chat(request: Request, body: ChatRequest):
    server_req_id = str(uuid.uuid4())[:8]
    client_req_id = request.headers.get("X-Client-Request-Id", "none")
    t_start = time.monotonic()

    # ── Message is already stripped by Pydantic validator ─────────────────────
    message = body.message  # guaranteed non-empty, max 1500 chars after validator

    # ── Persona normalisation ────────────────────────────────────────────────
    raw_persona = body.persona
    persona = normalize_persona(raw_persona)
    logger.info(
        f"POST /api/chat START | server_req={server_req_id} | client_req={client_req_id} "
        f"| ip={request.client.host} | persona_normalized={persona!r} "
        f"| msgLen={len(message)}"
        # NOTE: never log message content or IP-linked data beyond length
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

    # ── 1.5. Guided flow — runs BEFORE RAG / Gemini ─────────────────────────
    # Completely optional: if guidedFlow is absent the block is skipped.
    gf_input: GuidedFlowInput | None = body.guidedFlow

    if gf_input is not None:
        gf_active  = gf_input.active
        gf_step    = gf_input.step
        gf_state   = dict(gf_input.state or {})

        # Case A: flow is already active — advance it
        if gf_active and gf_step:
            result = guided_flow_service.update_guided_flow(
                body.message, gf_step, gf_state, persona
            )
            if not result.get("flow_complete", False):
                logger.info(f"[{server_req_id}] Guided flow ADVANCED | step={result.get('guided_flow_step')}")
                return _build_guided_response(result, persona)
            # flow_complete=True → fall through to normal RAG/Gemini
            logger.info(f"[{server_req_id}] Guided flow COMPLETE — handing off to normal pipeline")

        # Case B: flow not active yet — check if this message should trigger it
        elif not gf_active:
            if guided_flow_service.detect_guided_flow_trigger(body.message):
                result = guided_flow_service.start_guided_flow(persona)
                logger.info(f"[{server_req_id}] Guided flow TRIGGERED | persona={persona}")
                return _build_guided_response(result, persona)

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
        # Log error type only; NEVER log raw str(e) as it may contain key hints
        logger.error(
            f"[{server_req_id}] Config/auth error | type={type(e).__name__} | durationMs={elapsed}"
        )
        return JSONResponse(
            status_code=503,
            content={
                "answer": (
                    "The assistant is temporarily unavailable due to a configuration issue. "
                    "Please try again later, or check "
                    "[eci.gov.in](https://eci.gov.in) for official information."
                ),
                "sources": [],
                "safety": {"blocked": True, "reason": "service_unavailable"},
                "meta": {"used_model": False, "used_rag": False},
            },
        )

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

    except Exception as e:
        # Catch-all: unexpected errors — log full trace server-side, send safe JSON
        elapsed = round((time.monotonic() - t_start) * 1000)
        logger.error(
            f"[{server_req_id}] Unexpected error | type={type(e).__name__} | durationMs={elapsed}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "answer": (
                    "Something went wrong while preparing the answer. "
                    "Please try again, or check official ECI sources."
                ),
                "sources": [],
                "safety": {"blocked": True, "reason": "internal_error"},
                "meta": {"used_model": False, "used_rag": False},
            },
        )
