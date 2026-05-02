"""
Suggested reply registry and validation for VoteWise.

The backend owns every civic chip that can be shown in chat. Frontend code may
render these objects and may send the intent back, but it should not invent new
civic suggestion labels.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable


VALID_HANDLER_TYPES = {
    "direct_template",
    "guided_flow",
    "conversation_context",
    "gemini_intent",
    "safety_recovery",
    "out_of_scope_recovery",
}


@dataclass(frozen=True)
class SuggestedReplyItem:
    label: str
    intent: str
    domain: str
    required_context: str | None
    allowed_after_answer_sources: tuple[str, ...]
    blocked_after_answer_sources: tuple[str, ...]
    handler_type: str
    handler: str
    expected_response_summary: str
    fallback_behavior: str
    source_files: tuple[str, ...]

    @property
    def requires_context(self) -> bool:
        return bool(self.required_context)

    def as_response(self, label: str | None = None) -> dict[str, Any]:
        return {
            "id": self.intent,
            "label": label or self.label,
            "action": self.intent,
            "intent": self.intent,
            "domain": self.domain,
            "requires_context": self.requires_context,
            "context_type": self.required_context or "none",
            "handler": self.handler,
            "handler_type": self.handler_type,
        }

    def as_inventory_row(self, label: str | None = None) -> dict[str, Any]:
        return {
            "label": label or self.label,
            "source_file": ", ".join(self.source_files),
            "intended_intent": self.intent,
            "intended_domain": self.domain,
            "required_context": self.required_context or "none",
            "expected_response": self.expected_response_summary,
            "current_handler_exists": "yes" if self.handler_type in VALID_HANDLER_TYPES and self.handler else "no",
        }


def _item(
    label: str,
    intent: str,
    domain: str,
    handler_type: str,
    handler: str,
    expected: str,
    fallback: str,
    *,
    required_context: str | None = None,
    allowed: Iterable[str] = ("direct_template", "guided_flow", "gemini_verified", "gemini_grounded", "rag_grounded"),
    blocked: Iterable[str] = ("out_of_scope", "safety_refusal"),
    sources: Iterable[str] = ("server/app/services/suggested_reply_registry.py",),
) -> SuggestedReplyItem:
    return SuggestedReplyItem(
        label=label,
        intent=intent,
        domain=domain,
        required_context=required_context,
        allowed_after_answer_sources=tuple(allowed),
        blocked_after_answer_sources=tuple(blocked),
        handler_type=handler_type,
        handler=handler,
        expected_response_summary=expected,
        fallback_behavior=fallback,
        source_files=tuple(sources),
    )


_ITEMS: tuple[SuggestedReplyItem, ...] = (
    _item(
        "Guide me as a first-time voter",
        "start_first_time_voter",
        "voter_registration",
        "guided_flow",
        "guided_flow.start",
        "Start the guided voter journey and ask whether this is the user's first time voting.",
        "Start the first-time voter guide from the beginning.",
        sources=("client/src/hooks/useChat.js", "client/src/pages/ChatPage.jsx", "server/app/services/guided_flow_service.py"),
    ),
    _item(
        "I am 18 and want to vote",
        "start_first_time_voter_18",
        "voter_registration",
        "guided_flow",
        "guided_flow.start_already_18",
        "Start the voter journey and proceed toward checking whether the user has Voter ID/EPIC.",
        "Ask whether the user is voting for the first time.",
        sources=("client/src/hooks/useChat.js", "client/src/pages/ChatPage.jsx"),
    ),
    _item(
        "Yes, first time",
        "guided_yes_first_time",
        "voter_registration",
        "guided_flow",
        "guided_flow.ask_age_status",
        "Ask the user's age status.",
        "Ask whether the user is already 18, turning 18 soon, or under 18.",
        sources=("server/app/services/guided_flow_service.py",),
    ),
    _item(
        "No",
        "guided_no_returning",
        "voter_registration",
        "guided_flow",
        "guided_flow.returning_voter_path",
        "Give the returning-voter checklist: check name, find booth, carry accepted ID.",
        "Ask whether the user wants registration, voter list, booth, or polling-day help.",
        sources=("server/app/services/guided_flow_service.py",),
    ),
    _item(
        "I am already 18",
        "age_already_18",
        "voter_registration",
        "guided_flow",
        "guided_flow.ask_has_epic",
        "Ask whether the user has Voter ID/EPIC.",
        "Ask whether the user has Voter ID/EPIC.",
        sources=("server/app/services/guided_flow_service.py",),
    ),
    _item(
        "I will turn 18 soon",
        "age_turning_18_soon",
        "voter_registration",
        "guided_flow",
        "guided_flow.turning_18_path",
        "Explain qualifying-date caution and the Form 6 path.",
        "Explain that exact eligibility should be checked on official ECI sources.",
        sources=("server/app/services/guided_flow_service.py",),
    ),
    _item(
        "I am under 18",
        "age_under_18",
        "election_process",
        "guided_flow",
        "guided_flow.under_18_path",
        "Explain that the user cannot vote yet and offer election basics.",
        "Offer election-process basics until the user becomes eligible.",
        sources=("server/app/services/guided_flow_service.py",),
    ),
    _item(
        "I already have voter ID",
        "epic_yes",
        "voter_list",
        "guided_flow",
        "guided_flow.has_epic_path",
        "Give the path: check name, verify details, find booth, carry ID, vote.",
        "Ask whether the user wants help checking their name or finding their booth.",
        sources=("server/app/services/guided_flow_service.py",),
    ),
    _item(
        "I do not have voter ID",
        "epic_no",
        "voter_registration",
        "guided_flow",
        "guided_flow.no_epic_path",
        "Give the Form 6 registration path.",
        "Explain new-voter registration with Form 6.",
        sources=("server/app/services/guided_flow_service.py", "server/app/services/tone_service.py"),
    ),
    _item(
        "Not sure",
        "epic_not_sure",
        "voter_list",
        "guided_flow",
        "guided_flow.not_sure_epic",
        "Explain how to check Voter ID/EPIC status and offer registration steps.",
        "Offer both check-name and registration paths.",
        sources=("server/app/services/guided_flow_service.py",),
    ),
    _item(
        "What is Form 6?",
        "form6_definition",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.form6",
        "Explain Form 6 as the new-voter registration form.",
        "Explain Form 6 and point to voters.eci.gov.in.",
        sources=("server/app/services/tone_service.py", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "What should I do next?",
        "continue_next",
        "voter_registration",
        "conversation_context",
        "conversation_context.continue_next",
        "Continue the active voter journey with the next practical step.",
        "Ask whether the user wants next steps for registration, voter list, polling booth, or polling day.",
        required_context="active_or_recent_voter_journey",
        sources=("server/app/services/tone_service.py", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "What documents do I need?",
        "documents_registration",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.registration_documents",
        "Explain photo, age proof, and address proof for registration with official verification caution.",
        "Give general registration document guidance and ask the user to verify official requirements.",
        sources=("server/app/services/tone_service.py", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "Check my name",
        "check_name",
        "voter_list",
        "direct_template",
        "direct_answer_registry.voter_list",
        "Explain how to check the electoral roll/voter list.",
        "Direct the user to official voter-list search routes.",
        sources=("server/app/services/tone_service.py", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "How do I check my name?",
        "check_name_how",
        "voter_list",
        "direct_template",
        "direct_answer_registry.voter_list",
        "Explain how to check the electoral roll/voter list.",
        "Direct the user to official voter-list search routes.",
        sources=("client/src/hooks/useChat.js", "client/src/pages/ChatPage.jsx", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "Find polling booth",
        "find_polling_booth",
        "polling_day",
        "direct_template",
        "direct_answer_registry.polling_booth",
        "Explain official portal, helpline, state CEO, and BLO routes for finding the booth.",
        "Tell the user to use official voter details to find the assigned booth.",
        sources=("server/app/services/tone_service.py", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "What ID do I carry?",
        "documents_id",
        "polling_day",
        "direct_template",
        "direct_answer_registry.accepted_id",
        "Explain EPIC/Voter ID and accepted alternative photo IDs cautiously.",
        "Tell the user to verify the latest official ID list for the election.",
        sources=("server/app/services/tone_service.py", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "Explain polling day",
        "explain_polling_day",
        "polling_day",
        "direct_template",
        "direct_answer_registry.polling_day",
        "Explain arrival, verification, ink, EVM, VVPAT, and vote secrecy.",
        "Give a neutral polling-day walkthrough.",
        allowed=("safety_refusal", "direct_template", "guided_flow", "gemini_verified", "gemini_grounded", "rag_grounded"),
        blocked=("out_of_scope",),
        sources=("server/app/services/tone_service.py", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "What is EVM and VVPAT?",
        "evm_vvpat",
        "evm_vvpat",
        "direct_template",
        "direct_answer_registry.evm_vvpat",
        "Explain EVM and VVPAT simply.",
        "Explain EVM and VVPAT together.",
        sources=("client/src/hooks/useChat.js", "client/src/pages/ChatPage.jsx", "server/app/services/tone_service.py"),
    ),
    _item(
        "What is NOTA?",
        "nota_definition",
        "election_process",
        "direct_template",
        "direct_answer_registry.nota",
        "Explain None of the Above.",
        "Explain NOTA neutrally.",
        sources=("client/src/pages/ChatPage.jsx", "server/app/services/tone_service.py"),
    ),
    _item(
        "What is BLO?",
        "blo_definition",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.blo",
        "Explain Booth Level Officer.",
        "Explain BLO and keep it neutral.",
        sources=("server/app/services/direct_answer_registry.py",),
    ),
    _item(
        "What is MCC?",
        "mcc_definition",
        "election_process",
        "direct_template",
        "direct_answer_registry.mcc",
        "Explain Model Code of Conduct.",
        "Explain MCC neutrally.",
        sources=("server/app/services/direct_answer_registry.py",),
    ),
    _item(
        "Explain election process",
        "explain_election_process",
        "election_process",
        "direct_template",
        "direct_answer_registry.election_process",
        "Give a simple election-process overview.",
        "Explain the process from registration and voter list to polling and counting.",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "Explain Step 1",
        "explain_step_1",
        "voter_registration",
        "conversation_context",
        "conversation_context.step_reference",
        "Explain step 1 from the active path.",
        "Ask which journey the user wants if no path is active.",
        required_context="active_path_steps",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "Explain Step 2",
        "explain_step_2",
        "voter_registration",
        "conversation_context",
        "conversation_context.step_reference",
        "Explain step 2 from the active path.",
        "Ask which journey the user wants if no path is active.",
        required_context="active_path_steps",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "Explain Step 3",
        "explain_step_3",
        "voter_registration",
        "conversation_context",
        "conversation_context.step_reference",
        "Explain step 3 from the active path.",
        "Ask which journey the user wants if no path is active.",
        required_context="active_path_steps",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "Continue",
        "continue_journey",
        "voter_registration",
        "conversation_context",
        "conversation_context.continue_next",
        "Continue the active journey.",
        "Ask which journey the user wants if no context exists.",
        required_context="active_or_recent_voter_journey",
        sources=("server/app/services/tone_service.py", "server/app/services/conversation_context_service.py"),
    ),
    _item(
        "Start over",
        "start_over",
        "recovery",
        "out_of_scope_recovery",
        "recovery.start_over",
        "Reset guided flow and ask what the user wants help with.",
        "Restart to registration, voter list, polling booth, or polling day choices.",
        allowed=("out_of_scope", "safety_refusal", "direct_template", "guided_flow"),
        blocked=(),
        sources=("server/app/services/suggested_reply_registry.py",),
    ),
    _item(
        "Learn election process",
        "learn_election_process",
        "election_process",
        "direct_template",
        "direct_answer_registry.election_process",
        "Give an election-process overview.",
        "Explain the process from registration to results.",
        allowed=("safety_refusal", "direct_template", "guided_flow", "gemini_verified", "gemini_grounded", "rag_grounded"),
        blocked=("out_of_scope",),
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "What is vote privacy?",
        "vote_privacy",
        "polling_day",
        "direct_template",
        "direct_answer_registry.vote_privacy",
        "Explain secret ballot and that nobody can force or ask vote choice.",
        "Explain private, free voting and neutral reporting channels.",
        allowed=("safety_refusal", "direct_template", "guided_flow", "gemini_verified", "gemini_grounded", "rag_grounded"),
        blocked=("out_of_scope",),
        sources=("server/app/services/direct_answer_registry.py",),
    ),
    _item(
        "Ask about voter registration",
        "ask_voter_registration",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.voter_registration",
        "Explain the voter registration path.",
        "Give the Form 6 registration overview.",
        allowed=("out_of_scope", "safety_refusal", "direct_template", "guided_flow"),
        blocked=(),
        sources=("server/app/services/suggested_reply_registry.py",),
    ),
    _item(
        "Register as a voter",
        "register_as_voter",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.voter_registration",
        "Explain voter registration steps.",
        "Give the Form 6 registration overview.",
        sources=("server/app/services/guided_flow_service.py",),
    ),
    _item(
        "Voter registration",
        "registration_topic",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.voter_registration",
        "Explain voter registration steps.",
        "Give the Form 6 registration overview.",
        allowed=("out_of_scope", "safety_refusal", "direct_template"),
        blocked=(),
        sources=("server/app/services/conversation_context_service.py",),
    ),
    _item(
        "Checking my name",
        "checking_name_topic",
        "voter_list",
        "direct_template",
        "direct_answer_registry.voter_list",
        "Explain voter-list checking.",
        "Direct the user to official voter-list search routes.",
        allowed=("out_of_scope", "safety_refusal", "direct_template"),
        blocked=(),
        sources=("server/app/services/conversation_context_service.py",),
    ),
    _item(
        "Finding my booth",
        "finding_booth_topic",
        "polling_day",
        "direct_template",
        "direct_answer_registry.polling_booth",
        "Explain polling-booth lookup.",
        "Direct the user to official booth lookup routes.",
        allowed=("out_of_scope", "safety_refusal", "direct_template"),
        blocked=(),
        sources=("server/app/services/conversation_context_service.py",),
    ),
    _item(
        "Polling day",
        "polling_day_topic",
        "polling_day",
        "direct_template",
        "direct_answer_registry.polling_day",
        "Explain polling-day basics.",
        "Give a neutral polling-day walkthrough.",
        allowed=("out_of_scope", "safety_refusal", "direct_template"),
        blocked=(),
        sources=("server/app/services/conversation_context_service.py",),
    ),
    _item(
        "Explain more",
        "explain_more",
        "voter_registration",
        "conversation_context",
        "conversation_context.explain_current",
        "Explain the current topic in more detail.",
        "Ask which topic the user wants explained.",
        required_context="recent_topic",
        sources=("server/app/services/conversation_context_service.py",),
    ),
    _item(
        "Explain simply",
        "explain_simply",
        "election_process",
        "conversation_context",
        "conversation_context.explain_current_simple",
        "Explain the current topic simply.",
        "Ask which topic the user wants explained simply.",
        required_context="recent_topic",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "Give an example",
        "give_example",
        "election_process",
        "conversation_context",
        "conversation_context.example",
        "Give a simple example for the current topic.",
        "Ask which election topic the user wants an example for.",
        required_context="recent_topic",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "Why does this matter?",
        "why_matter",
        "election_process",
        "conversation_context",
        "conversation_context.why_matter",
        "Explain why the current topic matters civically.",
        "Ask which topic the user wants civic importance for.",
        required_context="recent_topic",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "Where do I apply?",
        "where_apply",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.where_apply",
        "Tell the user the official portal for voter services.",
        "Point to voters.eci.gov.in and official channels.",
        sources=("server/app/services/conversation_context_service.py",),
    ),
    _item(
        "Where do I do this?",
        "where_do_this",
        "voter_registration",
        "conversation_context",
        "conversation_context.where_to_do",
        "Use current topic to point to the right official route.",
        "Point to voters.eci.gov.in and ask which task they mean.",
        required_context="recent_topic",
        sources=("server/app/services/conversation_context_service.py",),
    ),
    _item(
        "Track my application",
        "track_application",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.track_application",
        "Explain official application tracking at the voter portal.",
        "Point to official tracking routes and reference number use.",
        sources=("server/app/services/conversation_context_service.py",),
    ),
    _item(
        "What is the qualifying date?",
        "qualifying_date",
        "voter_registration",
        "direct_template",
        "direct_answer_registry.qualifying_date",
        "Explain qualifying-date concept cautiously and ask user to verify current dates.",
        "Avoid guessing dates and refer to official ECI sources.",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "Election timeline",
        "election_timeline",
        "election_process",
        "direct_template",
        "direct_answer_registry.election_timeline",
        "Explain a generic election timeline without guessing current dates.",
        "Tell the user to verify live dates on ECI sources.",
        sources=("server/app/services/tone_service.py",),
    ),
    _item(
        "What is a coalition government?",
        "coalition_government",
        "government_institution",
        "direct_template",
        "direct_answer_registry.coalition_government",
        "Explain coalition government neutrally.",
        "Define coalition government without party preference.",
        sources=("client/src/pages/ChatPage.jsx",),
    ),
)


_ITEM_BY_INTENT = {item.intent: item for item in _ITEMS}


def _norm_label(label: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", (label or "").strip().lower().replace("-", " "))
    return " ".join(cleaned.split())


_LABEL_TO_INTENT: dict[str, str] = {
    _norm_label(item.label): item.intent
    for item in _ITEMS
}


_ALIASES: dict[str, str] = {
    # Guided-flow variants currently emitted by older backend/frontend code.
    "no i have voted before": "guided_no_returning",
    "yes i have voter id": "epic_yes",
    "yes i have voter id card": "epic_yes",
    "no i don't have one": "epic_no",
    "no i dont have one": "epic_no",
    "i don't have voter id": "epic_no",
    "i dont have voter id": "epic_no",
    "yes show me registration steps": "epic_no",
    "i found my voter id": "epic_yes",
    "i am 18 and want to vote for the first time": "start_first_time_voter_18",
    "i am 18 and want to vote": "start_first_time_voter_18",
    # Name-list variants.
    "how to check my name": "check_name_how",
    "how do i check my name in voter list": "check_name_how",
    "check my name in voter list": "check_name",
    "help me check my name": "check_name_how",
    "checking my name": "checking_name_topic",
    # Booth variants.
    "how to find my booth": "find_polling_booth",
    "find my polling booth": "find_polling_booth",
    "finding my booth": "finding_booth_topic",
    # ID/document variants.
    "what id do i carry": "documents_id",
    "what id can i carry": "documents_id",
    "what should i carry": "documents_id",
    "what documents are needed": "documents_registration",
    "what documents do i need": "documents_registration",
    # EVM/VVPAT variants.
    "what is evm and vvpat": "evm_vvpat",
    "what is evm vvpat": "evm_vvpat",
    "what is evm": "evm_vvpat",
    "what is vvpat": "evm_vvpat",
    # Context/action variants.
    "explain the first step": "explain_step_1",
    "explain form 6": "form6_definition",
    "continue": "continue_journey",
    "next step": "continue_journey",
    "tell me next step": "continue_journey",
    "what after that": "continue_journey",
    "explain slowly": "explain_simply",
    "how do i fill form 6": "register_as_voter",
    "how do i track application": "track_application",
    "what is the qualifying date": "qualifying_date",
    "how do elections work": "explain_election_process",
    "learn election basics": "learn_election_process",
    "understand polling day": "explain_polling_day",
    "understand election timeline": "election_timeline",
}

for _label, _intent in _ALIASES.items():
    _LABEL_TO_INTENT.setdefault(_norm_label(_label), _intent)


INITIAL_SUGGESTION_INTENTS = (
    "start_first_time_voter",
    "start_first_time_voter_18",
    "evm_vvpat",
    "check_name_how",
)

OUT_OF_SCOPE_RECOVERY_INTENTS = (
    "ask_voter_registration",
    "checking_name_topic",
    "finding_booth_topic",
    "polling_day_topic",
)

SAFETY_RECOVERY_INTENTS = (
    "learn_election_process",
    "vote_privacy",
    "explain_polling_day",
    "ask_voter_registration",
)

STALE_OPTION_RESPONSE = (
    "Let's restart that step. What do you want help with - registration, "
    "voter list, polling booth, or polling day?"
)

CLARIFY_CONTEXT_RESPONSE = (
    "Sure - which journey do you want help with: registration, voter list, "
    "polling booth, or polling day?"
)


def get_registry_item(intent: str | None) -> SuggestedReplyItem | None:
    return _ITEM_BY_INTENT.get((intent or "").strip())


def find_registry_item_by_label(label: str | None) -> SuggestedReplyItem | None:
    intent = _LABEL_TO_INTENT.get(_norm_label(label or ""))
    return get_registry_item(intent)


def normalize_suggestion(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, dict):
        item = get_registry_item(raw.get("intent")) or find_registry_item_by_label(raw.get("label"))
        return item.as_response() if item else None
    if isinstance(raw, str):
        item = find_registry_item_by_label(raw)
        return item.as_response() if item else None
    return None


def suggestions_for_intents(intents: Iterable[str]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    for intent in intents:
        item = get_registry_item(intent)
        if item:
            suggestions.append(item.as_response())
    return suggestions


def initial_suggestions() -> list[dict[str, Any]]:
    return suggestions_for_intents(INITIAL_SUGGESTION_INTENTS)


def recovery_suggestions(answer_source: str) -> list[dict[str, Any]]:
    if answer_source == "safety_refusal":
        return suggestions_for_intents(SAFETY_RECOVERY_INTENTS)
    return suggestions_for_intents(OUT_OF_SCOPE_RECOVERY_INTENTS)


def _context_has_path(context: dict[str, Any]) -> bool:
    if not context:
        return False
    if context.get("last_path_steps"):
        return True
    guided_state = context.get("guided_flow_state")
    return bool(isinstance(guided_state, dict) and guided_state.get("last_path_steps"))


def _context_has_recent_journey(context: dict[str, Any]) -> bool:
    return bool(context and (context.get("active") or context.get("flow_type") or _context_has_path(context)))


def _context_has_topic(context: dict[str, Any]) -> bool:
    return bool(context and (context.get("last_topic") or _context_has_recent_journey(context)))


def _has_required_context(item: SuggestedReplyItem, context: dict[str, Any]) -> bool:
    if not item.required_context:
        return True
    if item.required_context == "active_path_steps":
        return _context_has_path(context)
    if item.required_context == "active_or_recent_voter_journey":
        return _context_has_recent_journey(context)
    if item.required_context == "recent_topic":
        return _context_has_topic(context)
    return False


def validate_suggested_replies(
    suggestions: Iterable[Any] | None,
    answer_source: str,
    domain: str,
    intent: str,
    conversation_context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    context = conversation_context or {}
    valid: list[dict[str, Any]] = []
    seen_intents: set[str] = set()

    if answer_source == "out_of_scope":
        suggestions = recovery_suggestions("out_of_scope")
    elif answer_source == "safety_refusal":
        suggestions = recovery_suggestions("safety_refusal")

    for raw in suggestions or []:
        normalized = normalize_suggestion(raw)
        if not normalized:
            continue

        item = get_registry_item(normalized.get("intent"))
        if not item:
            continue
        if not item.handler or item.handler_type not in VALID_HANDLER_TYPES:
            continue
        if answer_source in item.blocked_after_answer_sources:
            continue
        if answer_source in {"out_of_scope", "safety_refusal"} and answer_source not in item.allowed_after_answer_sources:
            continue
        if not _has_required_context(item, context):
            continue
        if item.intent in seen_intents:
            continue
        if not normalized.get("label") or not normalized.get("intent") or not normalized.get("domain"):
            continue

        valid.append(normalized)
        seen_intents.add(item.intent)
        if len(valid) == 4:
            break

    return valid


def all_registered_options() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [item.as_inventory_row() for item in _ITEMS]
    for label, intent in sorted(_ALIASES.items()):
        item = get_registry_item(intent)
        if item:
            rows.append(item.as_inventory_row(label=label))
    return rows


def registry_entries() -> list[SuggestedReplyItem]:
    return list(_ITEMS)
