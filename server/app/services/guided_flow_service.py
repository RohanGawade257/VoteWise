"""
guided_flow_service.py — Lightweight guided voter journey for VoteWise.

This service sits as a PRE-PROCESSING layer BEFORE RAG/Gemini.
It does not replace the chat; it adds a state-driven question flow
that builds a personalised voter path for the user.

Design principles:
- One question at a time, never a form
- No sensitive data collected (no Aadhaar, phone, address)
- All real actions redirected to voters.eci.gov.in / eci.gov.in
- Works with all personas (general, first-time-voter, student, elderly)
- State lives in frontend only (no DB needed)
"""
import re
from app.utils.logging import get_logger
from app.services.tone_service import apply_tone_to_template, get_persona_suggested_replies

logger = get_logger("guided_flow_service")

# ---------------------------------------------------------------------------
# Trigger detection — which messages should START the guided flow
# ---------------------------------------------------------------------------

_TRIGGER_PATTERNS = [
    r"\bguide\s*me\b",
    r"\bfirst[\s-]?time\s*voter\b",
    r"\bfirst\s*time\s*vot(e|ing)\b",
    r"\bnew\s*voter\b",
    r"\bi\s*(am|m)\s*1?8\b",
    r"\bi\s*want\s*to\s*vote\b",
    r"\bhow\s*(do\s*i|can\s*i|to)\s*vote\b",
    r"\bhow\s*(do\s*i|can\s*i)\s*register\b",
    r"\bstart\s*(my\s*)?voter\b",
    r"\bvoting\s*for\s*the\s*first\s*time\b",
    r"\bfirst\s*election\b",
    r"\bnever\s*voted\b",
]
_TRIGGER_RE = [re.compile(p, re.IGNORECASE) for p in _TRIGGER_PATTERNS]

# ---------------------------------------------------------------------------
# Affirmative / negative detection
# ---------------------------------------------------------------------------

_YES_RE = re.compile(
    r"^(yes|yeah|yep|yup|haan|ha|sure|of\s*course|correct|right|i\s*am|i'm|absolutely|ok|okay|go\s*ahead)[\s!.,]*$",
    re.IGNORECASE
)
_NO_RE = re.compile(
    r"^(no|nope|nahi|na|not\s*yet|not\s*sure|maybe|i\s*don'?t\s*know|don'?t\s*know|not\s*really)[\s!.,]*$",
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Step definitions — each step knows what it asks and what comes next
# ---------------------------------------------------------------------------

GUIDED_STEPS = {

    "ask_first_time": {
        "question": lambda p: apply_tone_to_template("ask_first_time", p),
        "replies": ["Yes, first time", "No, I have voted before"],
    },

    "ask_age_status": {
        "question": lambda p: apply_tone_to_template("ask_age_status", p),
        "replies": ["I am already 18", "I will turn 18 soon", "I am under 18"],
    },

    "ask_has_epic": {
        "question": lambda p: apply_tone_to_template("ask_has_epic", p),
        "replies": ["Yes, I have Voter ID", "No, I don't have one", "Not sure"],
    },

    "ask_goal": {
        "question": lambda p: apply_tone_to_template("ask_goal", p),
        "replies": [
            "Register as a voter",
            "Check my name in voter list",
            "Find my polling booth",
            "Understand polling day",
            "Understand election timeline",
            "Learn election basics",
        ],
    },

    "show_path_no_epic": {
        "is_terminal": True,
    },

    "show_path_has_epic": {
        "is_terminal": True,
    },

    "show_path_turning_18": {
        "is_terminal": True,
    },

    "show_under_18": {
        "is_terminal": True,
    },

    "show_returning_voter": {
        "is_terminal": True,
    },
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_guided_flow_trigger(message: str) -> bool:
    """Return True if this message should kick off the guided voter flow."""
    return any(r.search(message) for r in _TRIGGER_RE)





def start_guided_flow(persona: str) -> dict:
    """
    Return the opening guided-flow response.
    Called when a trigger is detected and no flow is active.
    """
    step = "ask_first_time"
    question = GUIDED_STEPS[step]["question"](persona)
    replies = GUIDED_STEPS[step]["replies"]

    logger.info(f"Guided flow STARTED | persona={persona}")

    return {
        "answer": question,
        "guided_flow_step": step,
        "guided_flow_state": {},
        "suggested_replies": replies,
    }


def start_guided_flow_known_age(persona: str, age_status: str = "already_18") -> dict:
    """
    Start the guided flow when the clicked suggestion already tells us the
    user's age status. We still ask whether this is their first time voting so
    "No, I have voted before" can correctly branch to the returning-voter path.
    """
    step = "ask_first_time"
    question = GUIDED_STEPS[step]["question"](persona)
    replies = GUIDED_STEPS[step]["replies"]
    state = {"ageStatus": age_status}

    logger.info(f"Guided flow STARTED with known age | persona={persona} | age_status={age_status}")

    return {
        "answer": question,
        "guided_flow_step": step,
        "guided_flow_state": state,
        "suggested_replies": replies,
    }


def update_guided_flow(message: str, current_step: str, state: dict, persona: str) -> dict:
    """
    Advance the guided flow one step based on the user's reply.

    Returns:
        dict with keys: answer, guided_flow_step, guided_flow_state,
                        suggested_replies, flow_complete (bool)
    """
    msg_lower = message.lower().strip()
    new_state = dict(state)  # shallow copy so we don't mutate caller's dict

    # ── Step 1: ask_first_time → did they vote before? ──────────────────────
    if current_step == "ask_first_time":
        if _YES_RE.match(message) or "first" in msg_lower or "yes" in msg_lower:
            new_state["isFirstTimeVoter"] = True
            next_step = "ask_has_epic" if new_state.get("ageStatus") == "already_18" else "ask_age_status"
            q = GUIDED_STEPS[next_step]["question"](persona)
            replies = GUIDED_STEPS[next_step]["replies"]
            return _reply(q, next_step, new_state, replies)

        elif _NO_RE.match(message) or "before" in msg_lower or "already" in msg_lower or "have voted" in msg_lower:
            new_state["isFirstTimeVoter"] = False
            return _returning_voter_path(new_state, persona)

        else:
            # Unrecognised — re-ask with clarification
            return _reply(
                _tone(persona,
                    "I didn't quite catch that. Are you voting for the first time, or have you voted before?",
                    "No worries! Just tell me — is this your first time, or have you voted before? 😊",
                    "Hmm, could you say that again? Is this your first election or not?",
                    "Could you please clarify? Is this your first time voting?"
                ),
                current_step, new_state,
                GUIDED_STEPS[current_step]["replies"]
            )

    # ── Step 2: ask_age_status ───────────────────────────────────────────────
    if current_step == "ask_age_status":
        if "under 18" in msg_lower or ("under" in msg_lower and "18" in msg_lower):
            new_state["ageStatus"] = "under_18"
            return _under_18_path(new_state, persona)

        elif "soon" in msg_lower or "turning" in msg_lower or "will turn" in msg_lower:
            new_state["ageStatus"] = "turning_18_soon"
            return _turning_18_path(new_state, persona)

        elif "already" in msg_lower or "am 18" in msg_lower or "i'm 18" in msg_lower or "18" in msg_lower:
            new_state["ageStatus"] = "already_18"
            next_step = "ask_has_epic"
            q = GUIDED_STEPS[next_step]["question"](persona)
            replies = GUIDED_STEPS[next_step]["replies"]
            return _reply(q, next_step, new_state, replies)

        else:
            # Unrecognised — re-ask with clarification
            return _reply(
                apply_tone_to_template("reask_age_status", persona),
                current_step, new_state,
                GUIDED_STEPS[current_step]["replies"]
            )

    # ── Step 3: ask_has_epic ─────────────────────────────────────────────────
    if current_step == "ask_has_epic":
        # Check negatives first so "don't have" / "no I don't have" routes correctly
        _has_negation = any(neg in msg_lower for neg in ("don't have", "dont have", "no i don't", "do not have", "nahi", "no voter", "no id"))
        if _YES_RE.match(message) or ("yes" in msg_lower and not _has_negation) or ("have" in msg_lower and not _has_negation) or "voter id" in msg_lower and not _has_negation:
            new_state["hasEpic"] = "yes"
            return _has_epic_path(new_state, persona)

        elif "not sure" in msg_lower or "don't know" in msg_lower or "unsure" in msg_lower:
            new_state["hasEpic"] = "not_sure"
            return _reply(
                apply_tone_to_template("reask_has_epic", persona),
                "show_path_no_epic", new_state,
                ["Yes, show me registration steps", "I found my Voter ID"]
            )

        else:
            # Default: no EPIC
            new_state["hasEpic"] = "no"
            return _no_epic_path(new_state, persona)

    # ── Terminal path follow-up: user wants step-by-step detail ─────────────
    if current_step in ("show_path_no_epic", "show_path_has_epic",
                        "show_path_turning_18", "show_returning_voter",
                        "followup_accepted_id", "followup_voter_list",
                        "followup_form6", "followup_epic", "followup_booth",
                        "followup_polling_day", "followup_evm",
                        "followup_eligibility", "followup_docs", "followup_tracking"):
        # User replied to a terminal step. It has completed the GF lifecycle.
        # Fall through to Conversation Context / RAG
        return {"flow_complete": True, "guided_flow_state": new_state}

    # ── Unknown step fallback ────────────────────────────────────────────────
    logger.warning(f"Unknown guided flow step: {current_step}")
    return {"flow_complete": True, "guided_flow_state": new_state}


# ---------------------------------------------------------------------------
# Path builders
# ---------------------------------------------------------------------------

def _no_epic_path(state: dict, persona: str) -> dict:
    """Path for 18+ first-time voters with no Voter ID."""
    state["flow_type"] = "first_time_voter_no_epic"
    state["last_path_steps"] = [
        {"id": "check_eligibility", "title": "Check eligibility"},
        {"id": "register_form6", "title": "Register online (Form 6)"},
        {"id": "upload_docs", "title": "Upload documents"},
        {"id": "track_app", "title": "Track application"},
        {"id": "check_name", "title": "Check name in voter list"},
        {"id": "find_booth", "title": "Find polling booth"},
        {"id": "carry_id", "title": "Carry accepted ID and vote"}
    ]
    
    answer = apply_tone_to_template("show_path_no_epic", persona)
    return _reply(
        answer, "show_path_no_epic", state,
        get_persona_suggested_replies(persona, "no_epic_followups")
    )


def _has_epic_path(state: dict, persona: str) -> dict:
    """Path for voters who already have a Voter ID."""
    state["flow_type"] = "has_epic"
    state["last_path_steps"] = [
        {"id": "check_name", "title": "Check your name"},
        {"id": "verify_details", "title": "Verify details"},
        {"id": "find_booth", "title": "Find polling booth"},
        {"id": "carry_id", "title": "Carry accepted ID"},
        {"id": "vote", "title": "Vote using EVM"}
    ]

    answer = apply_tone_to_template("show_path_has_epic", persona)
    return _reply(
        answer, "show_path_has_epic", state,
        get_persona_suggested_replies(persona, "has_epic_followups")
    )


def _turning_18_path(state: dict, persona: str) -> dict:
    """Path for users turning 18 soon."""
    state["flow_type"] = "turning_18"
    state["last_path_steps"] = [
        {"id": "check_eligibility", "title": "Check qualifying date"},
        {"id": "register_form6", "title": "Register online (Form 6)"},
        {"id": "upload_docs", "title": "Prepare documents"}
    ]

    answer = apply_tone_to_template("show_path_turning_18", persona)
    return _reply(
        answer, "show_path_turning_18", state,
        get_persona_suggested_replies(persona, "turning_18_followups")
    )


def _under_18_path(state: dict, persona: str) -> dict:
    """Path for users under 18."""
    answer = apply_tone_to_template("show_under_18", persona)
    return _reply(
        answer, "show_under_18", state,
        get_persona_suggested_replies(persona, "under_18_followups")
    )


def _returning_voter_path(state: dict, persona: str) -> dict:
    """Path for users who have voted before."""
    state["flow_type"] = "returning_voter"
    state["last_path_steps"] = [
        {"id": "check_name", "title": "Check name"},
        {"id": "find_booth", "title": "Find polling booth"},
        {"id": "carry_id", "title": "Carry accepted ID"}
    ]
    answer = apply_tone_to_template("show_returning_voter", persona)
    return _reply(
        answer, "show_returning_voter", state,
        get_persona_suggested_replies(persona, "returning_voter_followups")
    )


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _reply(answer: str, step: str, state: dict, replies: list) -> dict:
    return {
        "answer": answer,
        "guided_flow_step": step,
        "guided_flow_state": state,
        "suggested_replies": replies,
        "flow_complete": False,
    }
