import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models import ChatRequest, ChatResponse, SafetyInfo, MetaInfo, SourceItem, GuidedFlowInput
from app.services import guided_flow_service
from app.services import safety_service, gemini_service, rag_service, conversation_context_service
from app.services.source_router import (
    classify_intent,
    CURRENT_ELECTION_FALLBACK,
    CURRENT_PARTY_FALLBACK,
    CURRENT_PUBLIC_FALLBACK,
)
from app.services.suggested_reply_registry import (
    CLARIFY_CONTEXT_RESPONSE,
    STALE_OPTION_RESPONSE,
    find_registry_item_by_label,
    get_registry_item,
    initial_suggestions,
    recovery_suggestions,
    suggestions_for_intents,
    validate_suggested_replies,
)
from app.services.llm_classifier_service import classify_intent_with_llm
from app.services.direct_answer_registry import get_direct_answer
from app.services.answer_verifier import verify_answer
from app.services.tone_service import apply_tone_to_template, normalize_persona
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
            answer_source="guided_flow",
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

def _apply_cc_to_response(resp: ChatResponse, cc_state: dict, context_reset: bool = False) -> ChatResponse:
    """Helper to append conversationContext state to responses."""
    if context_reset:
        resp.meta.context_reset = True
        resp.meta.conversation_context_active = False
    elif cc_state and cc_state.get("active"):
        resp.meta.conversation_context_active = True
        resp.meta.conversation_context = cc_state
        resp.meta.last_topic = cc_state.get("last_topic")
    return resp


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


def _official_sources(kind: str = "eci") -> list[SourceItem]:
    sources: list[SourceItem] = []
    if kind in {"voter", "all"}:
        sources.append(SourceItem(title="Voters' Services Portal", url="https://voters.eci.gov.in", type="official"))
    if kind in {"search", "all"}:
        sources.append(SourceItem(title="Electoral Search", url="https://electoralsearch.eci.gov.in", type="official"))
    sources.append(SourceItem(title="Election Commission of India", url="https://eci.gov.in", type="official"))
    seen: set[str] = set()
    unique: list[SourceItem] = []
    for source in sources:
        if source.url not in seen:
            unique.append(source)
            seen.add(source.url)
    return unique


def _context_from_request(body: ChatRequest) -> dict[str, Any]:
    context = body.conversationContext.model_dump() if body.conversationContext else {}
    gf = body.guidedFlow
    if gf and (gf.active or gf.state):
        guided_context = conversation_context_service.update_context_from_guided_flow({
            "guided_flow_step": gf.step,
            "guided_flow_state": gf.state or {},
        })
        merged = dict(guided_context)
        merged.update({k: v for k, v in context.items() if v not in (None, [], {}, False)})
        context = merged
    return context


def _validation_context(resp: ChatResponse) -> dict[str, Any]:
    context = dict(resp.meta.conversation_context or {})
    if resp.meta.conversation_context_active:
        context["active"] = True
    if resp.meta.last_topic and not context.get("last_topic"):
        context["last_topic"] = resp.meta.last_topic
    if resp.meta.guided_flow_state:
        context.setdefault("guided_flow_state", resp.meta.guided_flow_state)
        context.setdefault("last_path_steps", resp.meta.guided_flow_state.get("last_path_steps", []))
        context.setdefault("flow_type", resp.meta.guided_flow_state.get("flow_type"))
    if resp.meta.guided_flow_step:
        context.setdefault("guided_flow_step", resp.meta.guided_flow_step)
    return context


def _finalize_response(resp: ChatResponse, answer_source: str | None = None) -> ChatResponse:
    source = answer_source or resp.meta.answer_source or "unknown"
    resp.meta.answer_source = source
    context = _validation_context(resp)
    resp.meta.suggested_replies = validate_suggested_replies(
        resp.meta.suggested_replies,
        source,
        getattr(resp.meta, "domain", "unknown"),
        resp.meta.intent,
        context,
    )
    return resp


def _make_response(
    *,
    answer: str,
    persona: str,
    intent: str,
    answer_source: str,
    model: str = "direct",
    sources: list[SourceItem] | None = None,
    suggestions: Iterable[Any] | None = None,
    conversation_context: dict[str, Any] | None = None,
    safety: SafetyInfo | None = None,
) -> ChatResponse:
    context = conversation_context or {}
    meta = MetaInfo(
        model=model,
        used_rag=False,
        used_search_grounding=False,
        intent=intent,
        answer_source=answer_source,
        used_direct_answer=answer_source in {"direct_template", "conversation_context", "out_of_scope", "safety_refusal"},
        used_model=False,
        persona_used=persona,
        suggested_replies=list(suggestions or []),
        conversation_context_active=bool(context.get("active")),
        last_topic=context.get("last_topic"),
        last_action=context.get("last_action"),
        conversation_context=context if context.get("active") else {},
    )
    return _finalize_response(ChatResponse(
        answer=answer,
        sources=sources or [],
        safety=safety or SafetyInfo(blocked=False, reason=None),
        meta=meta,
    ), answer_source)


_DIRECT_NEXT: dict[str, tuple[str, ...]] = {
    "form6_definition": ("documents_registration", "where_apply", "track_application", "check_name_how"),
    "documents_registration": ("form6_definition", "where_apply", "track_application", "check_name_how"),
    "check_name": ("find_polling_booth", "documents_id", "explain_polling_day"),
    "check_name_how": ("find_polling_booth", "documents_id", "explain_polling_day"),
    "checking_name_topic": ("check_name_how", "find_polling_booth", "documents_id"),
    "find_polling_booth": ("documents_id", "explain_polling_day", "check_name_how"),
    "finding_booth_topic": ("find_polling_booth", "documents_id", "explain_polling_day"),
    "documents_id": ("check_name_how", "find_polling_booth", "explain_polling_day"),
    "explain_polling_day": ("documents_id", "evm_vvpat", "vote_privacy"),
    "polling_day_topic": ("explain_polling_day", "documents_id", "evm_vvpat"),
    "evm_vvpat": ("explain_polling_day", "nota_definition", "vote_privacy"),
    "nota_definition": ("evm_vvpat", "explain_election_process"),
    "blo_definition": ("check_name_how", "where_apply", "vote_privacy"),
    "mcc_definition": ("explain_election_process", "election_timeline"),
    "explain_election_process": ("evm_vvpat", "nota_definition", "election_timeline"),
    "learn_election_process": ("evm_vvpat", "nota_definition", "election_timeline"),
    "vote_privacy": ("explain_polling_day", "documents_id"),
    "ask_voter_registration": ("form6_definition", "documents_registration", "where_apply", "check_name_how"),
    "register_as_voter": ("form6_definition", "documents_registration", "where_apply", "check_name_how"),
    "registration_topic": ("form6_definition", "documents_registration", "where_apply", "check_name_how"),
    "where_apply": ("form6_definition", "documents_registration", "track_application"),
    "track_application": ("check_name_how", "where_apply"),
    "qualifying_date": ("form6_definition", "documents_registration", "where_apply"),
    "election_timeline": ("explain_election_process", "evm_vvpat", "nota_definition"),
    "coalition_government": ("explain_election_process", "election_timeline"),
}

_DIRECT_TOPIC: dict[str, str] = {
    "form6_definition": "form6",
    "documents_registration": "form6",
    "check_name": "voter_list",
    "check_name_how": "voter_list",
    "checking_name_topic": "voter_list",
    "find_polling_booth": "polling_booth",
    "finding_booth_topic": "polling_booth",
    "documents_id": "accepted_id",
    "explain_polling_day": "polling_day",
    "polling_day_topic": "polling_day",
    "evm_vvpat": "evm_vvpat",
    "nota_definition": "nota",
    "blo_definition": "blo",
    "mcc_definition": "mcc",
    "explain_election_process": "election_process",
    "learn_election_process": "election_process",
    "vote_privacy": "vote_privacy",
    "ask_voter_registration": "form6",
    "register_as_voter": "form6",
    "registration_topic": "form6",
    "where_apply": "form6",
    "track_application": "form6",
    "qualifying_date": "eligibility",
    "election_timeline": "election_process",
    "coalition_government": "coalition_government",
}


def _direct_text(intent: str, persona: str) -> str | None:
    classified_prompts = {
        "ask_voter_registration": "How do I register to vote?",
        "register_as_voter": "How do I register to vote?",
        "registration_topic": "How do I register to vote?",
        "check_name": "How do I check my name in voter list?",
        "check_name_how": "How do I check my name in voter list?",
        "checking_name_topic": "How do I check my name in voter list?",
        "explain_polling_day": "Explain polling day",
        "polling_day_topic": "Explain polling day",
        "evm_vvpat": "What is EVM and VVPAT?",
        "nota_definition": "What is NOTA?",
        "blo_definition": "What is BLO?",
        "vote_privacy": "Can a BLO ask who I vote for?",
        "coalition_government": "What is a coalition government?",
    }
    if intent in classified_prompts:
        result = classify_intent(classified_prompts[intent], persona=persona)
        return result.get("direct_response")

    if intent == "form6_definition":
        return apply_tone_to_template("followup_form6", persona)
    if intent == "documents_registration":
        return (
            "For new voter registration, you generally need:\n\n"
            "- A recent passport-size photo\n"
            "- Age proof, such as a birth certificate or school/college record\n"
            "- Address proof, such as Aadhaar, passport, utility bill, or another accepted document\n\n"
            "The exact documents can depend on the form and verification step, so check the upload instructions on "
            "[voters.eci.gov.in](https://voters.eci.gov.in) before submitting."
        )
    if intent in {"find_polling_booth", "finding_booth_topic"}:
        return apply_tone_to_template("followup_booth", persona)
    if intent == "documents_id":
        return apply_tone_to_template("followup_accepted_id", persona)
    if intent == "mcc_definition":
        return (
            "MCC stands for **Model Code of Conduct**. It is a set of rules that starts after elections are announced. "
            "It guides political parties, candidates, and governments so campaigning stays fair and official power is not misused.\n\n"
            "It covers things like campaign speeches, use of government resources, announcements by governments, and conduct near polling. "
            "For exact current instructions, verify from ECI notifications."
        )
    if intent in {"explain_election_process", "learn_election_process"}:
        return (
            "**Indian election process, simply:**\n\n"
            "1. The Election Commission announces the election schedule.\n"
            "2. Eligible citizens register and names are finalized in the voter list.\n"
            "3. Candidates file nominations and campaign under the Model Code of Conduct.\n"
            "4. Voters go to assigned polling stations, show ID, and vote using EVM/VVPAT.\n"
            "5. Votes are counted and results are officially declared.\n\n"
            "The exact dates change by election, so always check ECI sources for live schedules."
        )
    if intent == "where_apply":
        return (
            "Use the official **Voters' Services Portal**: [voters.eci.gov.in](https://voters.eci.gov.in).\n\n"
            "That is where you can apply for new voter registration with Form 6, check services, and track many voter-related requests. "
            "You can also verify information through ECI or your state Chief Electoral Officer website."
        )
    if intent == "track_application":
        return (
            "After submitting a voter registration or correction request, use your acknowledgement/reference number to track it on "
            "[voters.eci.gov.in](https://voters.eci.gov.in). If the portal asks for extra verification, follow only the official instructions shown there."
        )
    if intent == "qualifying_date":
        return (
            "The **qualifying date** is the official cut-off date used to decide whether someone is old enough to be included as a voter. "
            "India has used January 1 and additional qualifying dates for voter-roll updates, but exact current rules and deadlines should be verified on ECI sources.\n\n"
            "If you are turning 18 soon, check [voters.eci.gov.in](https://voters.eci.gov.in) and ECI notices before applying."
        )
    if intent == "election_timeline":
        return (
            "A typical election timeline is: schedule announcement, nominations, scrutiny and withdrawals, campaigning, polling day, counting, and result declaration. "
            "Live dates vary by election, so use [eci.gov.in](https://eci.gov.in) for current schedules."
        )
    return None


def _direct_response_for_intent(intent: str, persona: str) -> ChatResponse | None:
    answer = _direct_text(intent, persona)
    if not answer:
        return None
    topic = _DIRECT_TOPIC.get(intent)
    context = {
        "active": bool(topic),
        "flow_type": "topic_explainer",
        "last_topic": topic,
        "last_action": intent,
        "last_path_steps": [],
        "current_step_index": None,
        "awaiting_user_choice": False,
    }
    source_kind = "all" if intent in {
        "ask_voter_registration", "register_as_voter", "registration_topic",
        "form6_definition", "documents_registration", "check_name", "check_name_how",
        "checking_name_topic", "find_polling_booth", "finding_booth_topic",
        "documents_id", "where_apply", "track_application", "qualifying_date",
    } else "eci"
    return _make_response(
        answer=answer,
        persona=persona,
        intent=intent,
        answer_source="direct_template",
        sources=_official_sources(source_kind),
        suggestions=suggestions_for_intents(_DIRECT_NEXT.get(intent, ())),
        conversation_context=context,
    )


def _topic_from_context(context: dict[str, Any]) -> str | None:
    if not context:
        return None
    if context.get("last_topic"):
        return context["last_topic"]
    flow_type = context.get("flow_type")
    if flow_type == "returning_voter":
        return "returning_voter"
    if flow_type == "has_epic":
        return "voter_list"
    if flow_type == "turning_18":
        return "eligibility"
    if flow_type == "first_time_voter_no_epic":
        return "form6"
    return None


def _has_recent_context(context: dict[str, Any]) -> bool:
    return bool(context and (context.get("active") or context.get("last_topic") or context.get("flow_type") or context.get("last_path_steps")))


def _clarify_context_response(persona: str, intent: str = "clarify_context") -> ChatResponse:
    return _make_response(
        answer=CLARIFY_CONTEXT_RESPONSE,
        persona=persona,
        intent=intent,
        answer_source="conversation_context",
        suggestions=suggestions_for_intents(("ask_voter_registration", "checking_name_topic", "finding_booth_topic", "polling_day_topic")),
        conversation_context={},
    )


def _explain_topic_simply(topic: str, persona: str) -> str:
    text_by_topic = {
        "returning_voter": "Since you have voted before, you do not need the whole beginner path. Just re-check three things: your name is still on the voter list, your polling booth has not changed, and you have an accepted photo ID for polling day.",
        "form6": "Form 6 is the form for becoming a new voter. You fill it on the official voter portal, add basic details and documents, then wait for verification.",
        "eligibility": "Eligibility means checking whether you can register as a voter. In India, you generally need to be an Indian citizen, old enough under the official qualifying-date rule, and living in the area where you register.",
        "voter_list": "The voter list is the official list of people allowed to vote in an area. If your name is on it, officials can verify you at the booth.",
        "polling_booth": "Your polling booth is the exact place assigned to you for voting. Check it before election day so you go to the right location.",
        "accepted_id": "On polling day, carry a photo ID. Voter ID is best if you have it, and ECI may allow alternate photo IDs. Always check the official list for that election.",
        "polling_day": "On polling day, you go to your booth, show ID, get your finger marked, vote on the EVM, check the VVPAT slip, and leave peacefully.",
        "evm_vvpat": "EVM is the button machine used to cast your vote. VVPAT is the small printer window that shows your selected candidate briefly so you can verify the vote.",
        "nota": "NOTA means None of the Above. It lets a voter say they do not choose any listed candidate.",
        "mcc": "The Model Code of Conduct is a fairness rulebook for parties, candidates, and governments during elections.",
        "election_process": "An election moves from announcement, registration and voter lists, candidate nominations, campaigning, polling, counting, and results.",
        "vote_privacy": "Vote privacy means your choice is secret. No official, party worker, or other person can force you to reveal whom you voted for.",
        "coalition_government": "A coalition government forms when parties join together because no single party has enough seats alone.",
        "blo": "A BLO is a local election official who helps with voter-list and polling-area work. They do not decide your vote.",
    }
    answer = text_by_topic.get(topic, "This is part of your voter journey. Tell me whether you mean registration, voter list, polling booth, or polling day, and I will explain it simply.")
    if persona == "student":
        return answer
    if persona == "elderly":
        return answer.replace("re-check", "check again")
    return answer


def _continue_from_context(context: dict[str, Any], persona: str) -> ChatResponse:
    if not _has_recent_context(context):
        return _clarify_context_response(persona, "continue_next")

    topic = _topic_from_context(context)
    flow_type = context.get("flow_type")
    if flow_type == "returning_voter":
        answer = (
            "Your next best step is to check that your name is still in the voter list. "
            "After that, find your current polling booth and keep an accepted photo ID ready for polling day."
        )
        suggestions = ("check_name_how", "find_polling_booth", "documents_id")
        last_topic = "voter_list"
    elif topic in {"form6", "eligibility"}:
        answer = (
            "Your next step is to use Form 6 on voters.eci.gov.in if you are eligible. "
            "Keep your photo, age proof, and address proof ready. After submitting, track the application and then check your name in the voter list."
        )
        suggestions = ("documents_registration", "where_apply", "track_application", "check_name_how")
        last_topic = "form6"
    elif topic == "voter_list":
        answer = "Once your name is confirmed in the voter list, find your assigned polling booth and keep an accepted photo ID ready."
        suggestions = ("find_polling_booth", "documents_id", "explain_polling_day")
        last_topic = "polling_booth"
    elif topic == "polling_booth":
        answer = "After finding your polling booth, check what ID you can carry and review what happens on polling day."
        suggestions = ("documents_id", "explain_polling_day", "evm_vvpat")
        last_topic = "accepted_id"
    elif topic == "accepted_id":
        answer = "After keeping your accepted ID ready, go to your assigned booth on polling day, verify your name, and cast your vote privately."
        suggestions = ("explain_polling_day", "evm_vvpat", "vote_privacy")
        last_topic = "polling_day"
    else:
        steps = context.get("last_path_steps") or []
        if steps:
            answer = f"Start with Step 1: {steps[0].get('title', 'check your first step')}. I can explain that step or continue through the path."
            suggestions = ("explain_step_1", "continue_journey", "check_name_how")
            last_topic = topic or "voter_list"
        else:
            return _clarify_context_response(persona, "continue_next")

    new_context = dict(context)
    new_context.update({"active": True, "last_topic": last_topic, "last_action": "continue_next"})
    return _make_response(
        answer=answer,
        persona=persona,
        intent="continue_next",
        answer_source="conversation_context",
        suggestions=suggestions_for_intents(suggestions),
        conversation_context=new_context,
    )


def _explain_step_from_context(step_number: int, context: dict[str, Any], persona: str) -> ChatResponse:
    steps = context.get("last_path_steps") or context.get("guided_flow_state", {}).get("last_path_steps", [])
    if not steps or step_number < 1 or step_number > len(steps):
        return _clarify_context_response(persona, f"explain_step_{step_number}")

    step = steps[step_number - 1]
    step_id = step.get("id")
    title = step.get("title", f"Step {step_number}")
    detail_by_step = {
        "check_eligibility": "Check that you meet the voter eligibility rules before applying.",
        "register_form6": "Fill Form 6 on the official Voters' Services Portal to apply as a new voter.",
        "upload_docs": "Keep a photo, age proof, and address proof ready for the registration form.",
        "track_app": "Use your acknowledgement number on the portal to track your application.",
        "check_name": "Search the electoral roll to confirm your name appears before polling day.",
        "verify_details": "Check that your name, constituency, and other voter details are correct.",
        "find_booth": "Find the polling station assigned to your voter entry before election day.",
        "carry_id": "Carry your Voter ID or another accepted photo ID to the polling booth.",
        "vote": "At the booth, press the EVM button for your chosen candidate and verify the VVPAT slip.",
    }
    topic_by_step = {
        "check_eligibility": "eligibility",
        "register_form6": "form6",
        "upload_docs": "form6",
        "track_app": "form6",
        "check_name": "voter_list",
        "verify_details": "voter_list",
        "find_booth": "polling_booth",
        "carry_id": "accepted_id",
        "vote": "polling_day",
    }
    topic = topic_by_step.get(step_id, _topic_from_context(context) or "voter_list")
    new_context = dict(context)
    new_context.update({"active": True, "last_topic": topic, "last_action": f"explain_step_{step_number}"})
    return _make_response(
        answer=f"Step {step_number} is **{title}**. {detail_by_step.get(step_id, 'This is one part of your voter journey.')} ",
        persona=persona,
        intent=f"explain_step_{step_number}",
        answer_source="conversation_context",
        suggestions=suggestions_for_intents(("continue_journey", "explain_more", "where_do_this")),
        conversation_context=new_context,
    )


def _context_response_for_intent(intent: str, body: ChatRequest, persona: str, cc_state: dict[str, Any]) -> ChatResponse:
    context = cc_state or _context_from_request(body)
    if intent in {"continue_next", "continue_journey"}:
        return _continue_from_context(context, persona)
    if intent.startswith("explain_step_"):
        try:
            step_number = int(intent.rsplit("_", 1)[-1])
        except ValueError:
            step_number = 1
        return _explain_step_from_context(step_number, context, persona)
    if intent in {"explain_more", "explain_simply", "give_example", "why_matter", "where_do_this"}:
        if not _has_recent_context(context):
            return _clarify_context_response(persona, intent)
        topic = _topic_from_context(context)
        if intent == "where_do_this":
            return _make_response(
                answer="Use official voter services at [voters.eci.gov.in](https://voters.eci.gov.in). For voter-list search, use [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in).",
                persona=persona,
                intent=intent,
                answer_source="conversation_context",
                sources=_official_sources("all"),
                suggestions=suggestions_for_intents(("continue_journey", "check_name_how", "where_apply")),
                conversation_context={**context, "active": True, "last_action": intent},
            )
        if intent == "give_example":
            answer = f"Example: if your current topic is {topic or 'voter registration'}, the practical action is to use the official portal, complete the matching form or check, and verify the result before polling day."
        elif intent == "why_matter":
            answer = "This matters because voting only works smoothly when your name, booth, and ID are ready before polling day. It also helps protect your right to vote privately and confidently."
        else:
            answer = _explain_topic_simply(topic or "voter_list", persona)
        return _make_response(
            answer=answer,
            persona=persona,
            intent=intent,
            answer_source="conversation_context",
            suggestions=suggestions_for_intents(("continue_journey", "where_do_this", "check_name_how")),
            conversation_context={**context, "active": True, "last_topic": topic, "last_action": intent},
        )
    return _clarify_context_response(persona, intent)


def _guided_result_response(result: dict, persona: str, cc_state: dict[str, Any] | None = None, context_reset: bool = False) -> ChatResponse:
    resp = _build_guided_response(result, persona)
    step = result.get("guided_flow_step")
    state = result.get("guided_flow_state", {})
    if step in {"show_path_no_epic", "show_path_has_epic", "show_path_turning_18", "show_under_18", "show_returning_voter"}:
        resp = _apply_cc_to_response(resp, conversation_context_service.update_context_from_guided_flow(result))
    else:
        resp = _apply_cc_to_response(resp, cc_state or {}, context_reset=context_reset)
    return _finalize_response(resp, "guided_flow")


def _guided_response_for_intent(intent: str, body: ChatRequest, persona: str, cc_state: dict[str, Any]) -> ChatResponse:
    if intent == "start_first_time_voter":
        return _guided_result_response(guided_flow_service.start_guided_flow(persona), persona, cc_state, context_reset=True)
    if intent == "start_first_time_voter_18":
        return _guided_result_response(guided_flow_service.start_guided_flow_known_age(persona), persona, cc_state, context_reset=True)

    gf = body.guidedFlow
    current_step = gf.step if gf and gf.step else None
    state = dict(gf.state or {}) if gf else {}
    message_by_intent = {
        "guided_yes_first_time": ("ask_first_time", "Yes, first time"),
        "guided_no_returning": ("ask_first_time", "No, I have voted before"),
        "age_already_18": ("ask_age_status", "I am already 18"),
        "age_turning_18_soon": ("ask_age_status", "I will turn 18 soon"),
        "age_under_18": ("ask_age_status", "I am under 18"),
        "epic_yes": ("ask_has_epic", "Yes, I have Voter ID"),
        "epic_no": ("ask_has_epic", "No, I don't have one"),
        "epic_not_sure": ("ask_has_epic", "Not sure"),
    }
    fallback_step, exact_message = message_by_intent.get(intent, (current_step, body.message))
    result = guided_flow_service.update_guided_flow(
        exact_message,
        current_step or fallback_step,
        state,
        persona,
    )
    if result.get("flow_complete"):
        return _clarify_context_response(persona, intent)
    return _guided_result_response(result, persona, cc_state)


def _restart_response(persona: str) -> ChatResponse:
    resp = _make_response(
        answer="Let's start fresh. What do you want help with - registration, voter list, polling booth, or polling day?",
        persona=persona,
        intent="start_over",
        answer_source="out_of_scope",
        suggestions=initial_suggestions(),
        conversation_context={},
    )
    resp.meta.context_reset = True
    resp.meta.guided_flow_active = False
    resp.meta.guided_flow_step = None
    resp.meta.guided_flow_state = {}
    return _finalize_response(resp, "out_of_scope")


def _suggestion_item_from_request(body: ChatRequest):
    """
    Extract suggestion item from request. Priority:
    1. suggestion_id (direct intent ID from button click)
    2. suggestionIntent (alternative field name)
    3. suggestionId (legacy camelCase field)
    4. find_registry_item_by_label (backward compat for bare strings)
    """
    # Check all suggestion ID fields (prioritize snake_case)
    suggestion_id = body.suggestion_id or body.suggestionIntent or body.suggestionId
    if suggestion_id:
        item = get_registry_item(suggestion_id)
        if item:
            return item, suggestion_id
        # Invalid suggestion_id — return it anyway so backend can log it as stale
        return None, suggestion_id

    # Backward compatibility for old string-only frontend chips.
    # Only treat as button click if it's not a common user response like "yes"/"no".
    if body.message.strip().lower() not in {"yes", "no", "ok", "okay"}:
        item = find_registry_item_by_label(body.message)
        if item:
            return item, item.intent
    return None, None


def _handle_registered_suggestion(item, body: ChatRequest, persona: str, cc_state: dict[str, Any]) -> ChatResponse:
    logger.debug(
        "[suggestion-routing] message=%r | suggestion_id=%s | selected_handler=%s | previous_context=%s",
        body.message[:120],
        item.intent,
        item.handler,
        cc_state,
    )
    if item.intent == "start_over":
        return _restart_response(persona)
    if item.handler_type == "guided_flow":
        return _guided_response_for_intent(item.intent, body, persona, cc_state)
    if item.handler_type == "conversation_context":
        return _context_response_for_intent(item.intent, body, persona, cc_state)
    direct = _direct_response_for_intent(item.intent, persona)
    if direct:
        logger.debug("[suggestion-routing] next_suggestions=%s", direct.meta.suggested_replies)
        return direct
    return _make_response(
        answer=STALE_OPTION_RESPONSE,
        persona=persona,
        intent=item.intent,
        answer_source="out_of_scope",
        suggestions=recovery_suggestions("out_of_scope"),
    )


def _is_greeting_like(message: str) -> bool:
    return message.strip().lower() in {"hi", "hello", "hey", "namaste", "namaskar"}


def _is_clear_out_of_scope(message: str) -> bool:
    lower = message.lower()
    if _is_greeting_like(message) or rag_service.is_in_civic_scope(message) or guided_flow_service.detect_guided_flow_trigger(message):
        return False
    if any(phrase in lower for phrase in ("who are you", "what are you", "what can you do", "your name", "about yourself")):
        return False
    if any(word in lower for word in ("date", "time", "today")) and "election" not in lower:
        return False
    non_civic_markers = {
        "python", "javascript", "java", "cricket", "football", "movie", "recipe",
        "weather", "stock", "bitcoin", "instagram", "homework", "algebra",
    }
    if any(marker in lower for marker in non_civic_markers):
        return True
    return bool(re.match(r"^\s*(what|how|why|when|where|who)\b", lower))


def _out_of_scope_response(persona: str) -> ChatResponse:
    return _make_response(
        answer=apply_tone_to_template("out_of_scope", persona),
        persona=persona,
        intent="out_of_scope",
        answer_source="out_of_scope",
        suggestions=recovery_suggestions("out_of_scope"),
    )


@router.get("/api/suggestions/initial")
async def get_initial_suggested_replies():
    return {"suggestions": initial_suggestions()}



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
        return _finalize_response(ChatResponse(
            answer=safety_check["response"],
            sources=[],
            safety=SafetyInfo(blocked=True, reason=safety_check["reason"]),
            meta=MetaInfo(
                model="safety",
                used_rag=False,
                used_search_grounding=False,
                intent="political_persuasion_or_illegal",
                answer_source="safety_refusal",
                used_direct_answer=True,
                used_model=False,
                persona_used=persona,
                suggested_replies=recovery_suggestions("safety_refusal"),
            )
        ), "safety_refusal")
    logger.info(f"[{server_req_id}] Safety check PASSED")

    # ── 1.5. Guided flow — runs BEFORE RAG / Gemini ─────────────────────────
    gf_input: GuidedFlowInput | None = body.guidedFlow
    cc_input = body.conversationContext
    cc_state = cc_input.model_dump() if cc_input else {}

    # Determine if GF is currently active (frontend must send guidedFlow.active=true)
    gf_active = gf_input.active if gf_input is not None else False
    gf_step   = gf_input.step   if gf_input is not None else None
    gf_state  = dict(gf_input.state or {}) if gf_input is not None else {}

    suggestion_item, suggestion_identifier = _suggestion_item_from_request(body)
    logger.debug(
        f"[DBG][{server_req_id}] message={message[:120]!r} | suggestion_id={suggestion_identifier} "
        f"| guided_step={gf_step} | context={cc_state}"
    )
    if suggestion_identifier and not suggestion_item:
        logger.info(f"[{server_req_id}] Stale/invalid suggestion clicked | suggestion_id={suggestion_identifier}")
        return _make_response(
            answer=STALE_OPTION_RESPONSE,
            persona=persona,
            intent="stale_suggestion",
            answer_source="out_of_scope",
            suggestions=recovery_suggestions("out_of_scope"),
        )
    if suggestion_item:
        logger.info(f"[{server_req_id}] Suggestion routed exactly | intent={suggestion_item.intent} | handler={suggestion_item.handler}")
        return _handle_registered_suggestion(suggestion_item, body, persona, _context_from_request(body))

    if _is_clear_out_of_scope(message):
        logger.info(f"[{server_req_id}] Clear out-of-scope message | guided_active={gf_active}")
        return _out_of_scope_response(persona)

    # Case A: flow is already active — advance it
    if gf_active and gf_step:
        result = guided_flow_service.update_guided_flow(
            body.message, gf_step, gf_state, persona
        )
        if not result.get("flow_complete", False):
            logger.info(f"[{server_req_id}] Guided flow ADVANCED | step={result.get('guided_flow_step')}")
            return _guided_result_response(result, persona, cc_state)

        # flow_complete=True → fall through to normal RAG/Gemini
        logger.info(f"[{server_req_id}] Guided flow COMPLETE — handing off to normal pipeline")
        from app.services import conversation_context_service
        cc_state = conversation_context_service.update_context_from_guided_flow({
            "guided_flow_state": gf_state,
            "guided_flow_step": gf_step
        })

    # Case B: flow not active — check if this message should TRIGGER it
    elif not gf_active:
        if guided_flow_service.detect_guided_flow_trigger(body.message):
            result = guided_flow_service.start_guided_flow(persona)
            logger.info(f"[{server_req_id}] Guided flow TRIGGERED | persona={persona}")
            # Starting a guided flow RESETS the conversation context
            return _guided_result_response(result, persona, cc_state, context_reset=True)

    # ── 1.6. Conversation Context Follow-up ──────────────────────────────────
    from app.services import conversation_context_service
    if cc_state and cc_state.get("active"):
        followup_resp = conversation_context_service.handle_followup(body.message, cc_state, persona)
        if followup_resp:
            logger.info(f"[{server_req_id}] Contextual Follow-up MATCHED | intent={followup_resp.get('followup_intent')}")
            cc_state["last_topic"] = followup_resp.get("last_topic")
            return _finalize_response(ChatResponse(
                answer=followup_resp["answer"],
                sources=[],
                safety=SafetyInfo(blocked=False, reason=None),
                meta=MetaInfo(
                    model="conversation-context",
                    used_rag=False,
                    used_search_grounding=False,
                    intent="contextual_followup",
                    answer_source="conversation_context",
                    contextual_followup_intent=followup_resp["followup_intent"],
                    used_direct_answer=True,
                    used_model=False,
                    persona_used=persona,
                    conversation_context_active=True,
                    last_topic=cc_state["last_topic"],
                    conversation_context=cc_state,
                    suggested_replies=followup_resp.get("suggested_replies", [])
                )
            ), "conversation_context")

    # ── 2. Intent classification ─────────────────────────────────────────────
    intent_result = classify_intent(body.message, context=body.context, persona=persona)
    intent = intent_result["intent"]
    direct_response = intent_result.get("direct_response")
    use_rag = intent_result.get("use_rag", True)
    use_model = intent_result.get("use_model", True)
    logger.info(f"[{server_req_id}] Persona instruction applied | persona={persona} | intent={intent}")

    # --- LLM EXACT INTENT CLASSIFICATION ---
    llm_classification = None
    if intent == "civic_static" or intent == "general":
        llm_classification = await classify_intent_with_llm(body.message)
        if llm_classification.get("confidence") == "high":
            specific_intent = llm_classification.get("specific_intent")
            exact_answer = get_direct_answer(specific_intent)
            if exact_answer:
                direct_response = exact_answer
                intent = specific_intent
                use_rag = False
                use_model = False
                logger.info(f"[{server_req_id}] LLM Classifier matched exact intent: {intent}")

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

        classifier_next = {
            "voter_registration": ("form6_definition", "documents_registration", "where_apply", "check_name_how"),
            "evm_vvpat": ("explain_polling_day", "nota_definition", "vote_privacy"),
            "nota": ("evm_vvpat", "explain_election_process"),
            "coalition_government": ("explain_election_process", "election_timeline"),
            "polling_day": ("documents_id", "evm_vvpat", "vote_privacy"),
            "voter_list_check": ("find_polling_booth", "documents_id", "explain_polling_day"),
            "blo_explanation": ("check_name_how", "where_apply", "vote_privacy"),
            "vote_privacy": ("explain_polling_day", "documents_id"),
        }
        classifier_topic = {
            "voter_registration": "form6",
            "evm_vvpat": "evm_vvpat",
            "nota": "nota",
            "coalition_government": "coalition_government",
            "polling_day": "polling_day",
            "voter_list_check": "voter_list",
            "blo_explanation": "blo",
            "vote_privacy": "vote_privacy",
        }
        context_for_direct = dict(cc_state or {})
        if intent in classifier_topic:
            context_for_direct.update({
                "active": True,
                "flow_type": "topic_explainer",
                "last_topic": classifier_topic[intent],
                "last_action": intent,
            })

        direct_resp = ChatResponse(
            answer=direct_response,
            sources=[] if is_live_intent else _official_sources("all" if intent in {"voter_registration", "voter_list_check"} else "eci"),
            safety=SafetyInfo(blocked=False, reason=None),
            meta=MetaInfo(
                model="direct",
                used_rag=False,
                used_search_grounding=False,
                intent=intent,
                answer_source="direct_template",
                used_direct_answer=True,
                used_model=False,
                persona_used=persona,
                checkedAt=checked_at,
                sourceType=source_type,
                suggested_replies=suggestions_for_intents(classifier_next.get(intent, ())),
                conversation_context_active=bool(context_for_direct.get("active")),
                last_topic=context_for_direct.get("last_topic"),
                conversation_context=context_for_direct if context_for_direct.get("active") else {},
            )
        )
        return _finalize_response(direct_resp, "direct_template")
    elif direct_response is not None and skip_direct:
        logger.info(f"[{server_req_id}] Skipping direct fallback because grounding is ENABLED | intent={intent}")
        logger.debug(f"[DBG][{server_req_id}] skipped fallback because grounding enabled=True")

    # ── 4. RAG + Gemini flow ─────────────────────────────────────────────────
    # Handles: civic_static, political_party_neutral, unclear_followup (with context),
    # current_election_info, current_party_info, current_public_info (when grounding enabled)
    logger.debug(f"[DBG][{server_req_id}] gemini_service called=True")
    try:
        logger.info(f"[{server_req_id}] Calling gemini_service | intent={intent} | use_rag={use_rag} | grounding_enabled={grounding_enabled}")
        
        # Pass intent_type to RAG if available from LLM classification
        intent_type = llm_classification.get("intent_type") if llm_classification else None
        
        response = await gemini_service.generate_chat_response(
            message=body.message,
            persona=body.persona,
            context=body.context,
            intent=intent,
            use_rag=use_rag,
            intent_type=intent_type,
        )
        elapsed = round((time.monotonic() - t_start) * 1000)

        # Verify answer quality
        if llm_classification and llm_classification.get("confidence") == "high":
            is_valid = verify_answer(response.answer, llm_classification.get("intent_type"), llm_classification.get("specific_intent"))
            if not is_valid:
                logger.warning(f"[{server_req_id}] Answer verifier rejected response for intent {intent}. Using safe fallback.")
                fallback_ans = get_direct_answer(llm_classification.get("specific_intent"))
                if fallback_ans:
                    response.answer = fallback_ans
                    response.meta.used_rag = False
                    response.meta.answer_source = "verified_fallback"

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
            
        # Add CC if active
        response = _apply_cc_to_response(response, cc_state)

        response.meta.answer_source = "gemini_grounded" if response.meta.used_search_grounding else "gemini_verified"
        return _finalize_response(response, response.meta.answer_source)

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
            return _finalize_response(_apply_cc_to_response(ChatResponse(
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
                    answer_source="direct_template",
                    used_direct_answer=False,
                    used_model=True,  # Gemini was called (but failed)
                    persona_used=persona,
                    checkedAt=checked_at,
                    sourceType="unverified_fallback"
                )
            ), cc_state), "direct_template")

        # Standard RAG fallback for civic/static questions
        logger.warning(
            f"[{server_req_id}] Gemini unavailable — using RAG fallback "
            f"| reason={fallback_reason} | durationMs={elapsed} | err={err_str[:80]}"
        )
        fallback = _build_rag_fallback(body.message, body.persona, fallback_reason)
        fallback.meta.intent = intent
        fallback.meta.persona_used = persona
        fallback.meta.answer_source = "rag_grounded"
        return _finalize_response(_apply_cc_to_response(fallback, cc_state), "rag_grounded")

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
