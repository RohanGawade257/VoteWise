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
# Follow-up Intent Detection (Phase 2)
# ---------------------------------------------------------------------------

_FOLLOWUP_PATTERNS = {
    "accepted_id": [
        r"what\s*id\s*(do|should)\s*i\s*carry", r"which\s*id", r"documents\s*to\s*carry",
        r"id\s*proof", r"what\s*proof", r"what\s*card\s*should\s*i\s*take", r"accepted\s*id"
    ],
    "epic_explanation": [
        r"what\s*is\s*epic", r"what\s*is\s*(a\s*)?voter\s*id", r"epic\s*means"
    ],
    "voter_list_check": [
        r"how\s*to\s*check\s*(my\s*)?name", r"where\s*to\s*check\s*name", r"voter\s*list"
    ],
    "polling_booth": [
        r"find\s*(my\s*)?booth", r"where\s*to\s*vote", r"polling\s*station", r"where\s*is\s*my\s*booth"
    ],
    "form6_explanation": [
        r"what\s*is\s*form\s*6", r"how\s*to\s*register", r"new\s*voter\s*form", r"explain\s*form\s*6"
    ],
    "polling_day": [
        r"what\s*happens\s*on\s*polling\s*day", r"polling\s*day", r"how\s*do\s*i\s*vote\s*on\s*polling\s*day"
    ],
    "evm_vvpat": [
        r"explain\s*evm", r"what\s*is\s*evm", r"vvpat", r"how\s*to\s*use\s*evm"
    ],
    "explain_step": [
        r"explain\s*step\s*(\d+)", r"what\s*is\s*step\s*(\d+)", r"tell\s*me\s*(more\s*)?about\s*step\s*(\d+)", r"step\s*(\d+)"
    ]
}

_FOLLOWUP_RE = {
    intent: [re.compile(p, re.IGNORECASE) for p in patterns]
    for intent, patterns in _FOLLOWUP_PATTERNS.items()
}

# ---------------------------------------------------------------------------
# Persona-aware tone helpers
# ---------------------------------------------------------------------------

def _tone(persona: str, general: str, ftv: str, student: str, elderly: str) -> str:
    if persona == "first-time-voter":
        return ftv
    if persona == "student":
        return student
    if persona == "elderly":
        return elderly
    return general


# ---------------------------------------------------------------------------
# Step definitions — each step knows what it asks and what comes next
# ---------------------------------------------------------------------------

GUIDED_STEPS = {

    "ask_first_time": {
        "question": lambda p: _tone(p,
            "Are you voting for the first time?",
            "Exciting! Is this your first time voting? 🗳️",
            "Is this going to be your very first time voting?",
            "Will this be your first time voting?"
        ),
        "replies": ["Yes, first time", "No, I have voted before"],
    },

    "ask_age_status": {
        "question": lambda p: _tone(p,
            "Are you already 18, or will you turn 18 soon?",
            "Great! Are you already 18 years old, or will you be turning 18 soon?",
            "Are you 18 yet, or will you turn 18 soon?",
            "How old are you? Are you already 18 or turning 18 soon?"
        ),
        "replies": ["I am already 18", "I will turn 18 soon", "I am under 18"],
    },

    "ask_has_epic": {
        "question": lambda p: _tone(p,
            "Do you already have a Voter ID card (also called EPIC)?",
            "Do you have a Voter ID card yet? It's also called your EPIC number.",
            "Do you have a Voter ID card (EPIC) already?",
            "Do you have your Voter ID card ready?"
        ),
        "replies": ["Yes, I have Voter ID", "No, I don't have one", "Not sure"],
    },

    "ask_goal": {
        "question": lambda p: _tone(p,
            "What would you like help with today?",
            "What can I help you with today? Choose one or just type your question!",
            "What do you want to learn about? Pick one!",
            "What do you need help with? Take your time."
        ),
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


def detect_contextual_followup(message: str, state: dict) -> str | None:
    """
    Detect if the message is a short follow-up to the current guided flow state.
    Returns the intent string (e.g., 'accepted_id') or None.
    """
    # Check if the state has active path context
    if not state.get("flow_type"):
        return None

    msg_lower = message.lower().strip()
    
    # 1. Check exact step matches
    for pattern in _FOLLOWUP_RE["explain_step"]:
        match = pattern.search(msg_lower)
        if match:
            step_num = match.group(1)
            return f"explain_step_{step_num}"

    # 2. Check general follow-up intents
    for intent, patterns in _FOLLOWUP_RE.items():
        if intent == "explain_step": continue
        if any(p.search(msg_lower) for p in patterns):
            return intent

    return None

def handle_contextual_followup(intent: str, state: dict, persona: str) -> dict | None:
    """
    Return the response dict for a contextual followup.
    """
    # ── Map step explanation to actual topics ──
    if intent.startswith("explain_step_"):
        step_num_str = intent.split("_")[-1]
        try:
            step_idx = int(step_num_str) - 1
            steps = state.get("last_path_steps", [])
            if 0 <= step_idx < len(steps):
                step_id = steps[step_idx]["id"]
                # Remap the intent to the step's actual topic
                intent_map = {
                    "check_eligibility": "eligibility_explanation",
                    "upload_docs": "docs_explanation",
                    "track_app": "tracking_explanation",
                    "verify_details": "voter_list_check",
                    "check_name": "voter_list_check",
                    "register_form6": "form6_explanation",
                    "find_booth": "polling_booth",
                    "carry_id": "accepted_id",
                    "vote": "polling_day"
                }
                intent = intent_map.get(step_id, intent)
        except ValueError:
            pass

    # ── Responses ──
    resp = None
    if intent == "eligibility_explanation":
        ans = _tone(persona,
            "To be eligible to vote in India, you must be a citizen of India, at least 18 years old on the qualifying date (usually January 1 of the year), and a resident of the polling area. You must not be disqualified due to corrupt practices or other legal reasons.",
            "To vote, you just need to be an Indian citizen and 18 years old! You also need to live in the area where you want to vote.",
            "You can vote if you are an Indian citizen and 18 years old.",
            "You are eligible to vote if you are an Indian citizen, 18 years of age, and a resident of the area."
        )
        resp = _reply(ans, "followup_eligibility", state, ["Explain Form 6", "What documents do I need?"])
        
    elif intent == "docs_explanation":
        ans = _tone(persona,
            "When registering to vote via Form 6, you generally need to upload: 1) A recent passport-sized photograph. 2) Proof of Age (like a birth certificate, 10th/12th mark sheet, Aadhaar, or PAN card). 3) Proof of Address (like an Aadhaar card, electricity bill, passport, or bank passbook).",
            "When you fill out the form, keep a nice passport photo ready! You'll also need a document showing your age (like your 10th mark sheet or Aadhaar) and a document showing where you live (like Aadhaar or a recent electricity bill).",
            "You need a photo, something that shows how old you are, and something that shows where you live.",
            "Please keep a passport photo, age proof, and address proof ready for your application."
        )
        resp = _reply(ans, "followup_docs", state, ["Explain Form 6", "How do I track application?"])
        
    elif intent == "tracking_explanation":
        ans = "After submitting Form 6, you will receive a reference number. You can use this reference number on [voters.eci.gov.in](https://voters.eci.gov.in) to track the status of your application. Once approved, your name will be added to the electoral roll."
        resp = _reply(ans, "followup_tracking", state, ["How do I check my name?", "What ID do I carry?"])

    elif intent == "accepted_id":
        ans = _tone(persona,
            "First, make sure your name is in the voter list. On polling day, carry your EPIC/Voter ID if you have it. If you do not have EPIC, ECI allows alternative photo ID documents. Common examples include Aadhaar Card, PAN Card, Driving Licence, Passport, MNREGA Job Card, bank/post office passbook with photograph, pension document with photograph, service identity card, and UDID card.\n\nThe accepted list can change for a specific election, so verify from [eci.gov.in](https://eci.gov.in) or your state CEO website before polling day.",
            "You need to bring a valid photo ID to the polling booth. The best one is your Voter ID (EPIC). But if you don't have it, don't worry! You can bring your Aadhaar Card, PAN Card, Passport, or Driving Licence instead. Make sure your name is already on the voter list first! Check [eci.gov.in](https://eci.gov.in) for the full list of allowed IDs.",
            "To vote, you need to show an ID card at the booth. You can show your Voter ID, or other official cards like Aadhaar, PAN card, or Passport. It's to prove you are really you! But remember, you can only vote if your name is already written in the voter list.",
            "When you go to vote, please take your Voter ID card. If you don't have it, you can take your Aadhaar card, PAN card, or Passport. Just make sure your name is on the voter list first."
        )
        resp = _reply(ans, "followup_accepted_id", state, ["How do I check my name?", "Find polling booth"])

    elif intent == "voter_list_check":
        ans = _tone(persona,
            "You can check your name in the electoral roll by visiting the official portal: [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). You can search by your EPIC number, your personal details, or your mobile number.",
            "It's super easy to check! Just go to [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in) and enter your EPIC number, or search using your name and state.",
            "You can check if your name is on the list by going to a website called [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in).",
            "Please visit [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in) to check if your name is in the voter list. You can search using your Voter ID number."
        )
        resp = _reply(ans, "followup_voter_list", state, ["What ID do I carry?", "Find polling booth"])

    elif intent == "form6_explanation":
        ans = _tone(persona,
            "**Form 6** is the official application form for new voters to register in the electoral roll. You can fill it online at [voters.eci.gov.in](https://voters.eci.gov.in) or submit a physical copy to your Electoral Registration Officer. You will need a passport-sized photograph, age proof, and address proof.",
            "**Form 6** is what you fill out to become a registered voter! You can do it all online at [voters.eci.gov.in](https://voters.eci.gov.in). Just upload your photo, a proof of your age (like a birth certificate), and a proof of your address.",
            "**Form 6** is a form you fill out to tell the government you want to be a voter. You can do it on the internet at [voters.eci.gov.in](https://voters.eci.gov.in).",
            "**Form 6** is the form you use to register as a new voter. You can fill it out on the website [voters.eci.gov.in](https://voters.eci.gov.in)."
        )
        resp = _reply(ans, "followup_form6", state, ["How do I check my name?", "What ID do I carry?"])

    elif intent == "epic_explanation":
        ans = "EPIC stands for **Electors Photo Identity Card**. It is commonly known as your **Voter ID card**. It contains your photograph, name, address, and a unique EPIC number. You can use it as ID on polling day, but remember, having an EPIC is not enough — your name must also be in the current voter list!"
        resp = _reply(ans, "followup_epic", state, ["How do I check my name?", "What ID do I carry?"])

    elif intent == "polling_booth":
        ans = "Your polling booth is the specific location where you go to cast your vote. You can find your exact polling booth details by searching your name at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in) or by calling the Voter Helpline at **1950**."
        resp = _reply(ans, "followup_booth", state, ["What ID do I carry?", "Explain polling day"])

    elif intent == "polling_day":
        ans = "On polling day, you go to your assigned polling booth. First, a polling officer checks your name in the voter list and your ID. Then, your finger is marked with indelible ink. Finally, you go to the voting compartment, press the button next to your chosen candidate on the EVM, and a VVPAT slip prints to confirm your vote."
        resp = _reply(ans, "followup_polling_day", state, ["What ID do I carry?", "What is EVM?"])
        
    elif intent == "evm_vvpat":
        ans = "**EVM** (Electronic Voting Machine) is the machine where you press a button to cast your vote. **VVPAT** (Voter Verifiable Paper Audit Trail) is a printer attached to the EVM. When you vote, it prints a paper slip showing your choice. The slip is visible for 7 seconds behind glass so you can verify your vote, then it drops into a sealed box."
        resp = _reply(ans, "followup_evm", state, ["Explain polling day", "What ID do I carry?"])

    if resp:
        resp["contextual_followup_intent"] = intent

    return resp


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
            next_step = "ask_age_status"
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
            return _reply(
                _tone(persona,
                    "Please choose: are you already 18, turning 18 soon, or under 18?",
                    "Just tell me — are you 18 already, turning 18 soon, or younger than 18?",
                    "Are you already 18, about to turn 18, or younger than 18?",
                    "Please let me know: are you 18 or older, turning 18 soon, or younger?"
                ),
                current_step, new_state,
                GUIDED_STEPS[current_step]["replies"]
            )

    # ── Step 3: ask_has_epic ─────────────────────────────────────────────────
    if current_step == "ask_has_epic":
        if _YES_RE.match(message) or "yes" in msg_lower or "have" in msg_lower or "voter id" in msg_lower:
            new_state["hasEpic"] = "yes"
            return _has_epic_path(new_state, persona)

        elif "not sure" in msg_lower or "don't know" in msg_lower or "unsure" in msg_lower:
            new_state["hasEpic"] = "not_sure"
            return _reply(
                _tone(persona,
                    "No problem! You can check if you have a Voter ID by searching at "
                    "[electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). "
                    "Would you like me to show you the registration steps just in case?",
                    "That's okay! You can check your Voter ID status at "
                    "[electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). "
                    "Shall I walk you through registering from scratch?",
                    "You can find out at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). "
                    "Want me to show the registration steps?",
                    "You can check at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in). "
                    "Shall I explain how to register?"
                ),
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
        # User replied to a terminal step
        # Phase 1/2: check for contextual followup FIRST
        followup_intent = detect_contextual_followup(message, new_state)
        if followup_intent:
            resp = handle_contextual_followup(followup_intent, new_state, persona)
            if resp:
                return resp
        
        # If no contextual followup matched, hand off to normal RAG/Gemini
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
    
    answer = _tone(persona,
        (
            "**Your First-Time Voter Path**\n\n"
            "Since you are 18+ and don't have a Voter ID yet, here are your steps:\n\n"
            "- **Step 1 — Check eligibility:** Must be 18+, Indian citizen, and resident of your constituency\n"
            "- **Step 2 — Register online:** Go to [voters.eci.gov.in](https://voters.eci.gov.in) and fill **Form 6**\n"
            "- **Step 3 — Upload documents:** Passport photo, age proof (birth certificate or 10th mark sheet), address proof\n"
            "- **Step 4 — Track your application:** Use your reference number on the portal\n"
            "- **Step 5 — Check your name in the voter list:** Verify at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n"
            "- **Step 6 — Find your polling booth:** Check on [voters.eci.gov.in](https://voters.eci.gov.in) or call **1950**\n"
            "- **Step 7 — Vote on polling day:** Carry an accepted ID and use the EVM\n\n"
            "> All registration must be done on [voters.eci.gov.in](https://voters.eci.gov.in). VoteWise cannot register you.\n\n"
            "Which step would you like me to explain in detail?"
        ),
        (
            "**You're on your way! 🎉 Here's your personalised voter journey:**\n\n"
            "- ✅ **Step 1 — Check eligibility:** 18+, Indian citizen, and resident of your area\n"
            "- ✅ **Step 2 — Register with Form 6:** Visit [voters.eci.gov.in](https://voters.eci.gov.in)\n"
            "- ✅ **Step 3 — Upload documents:** Photo, age proof, address proof\n"
            "- ✅ **Step 4 — Track your application** using your reference number\n"
            "- ✅ **Step 5 — Verify your name** in the voter list\n"
            "- ✅ **Step 6 — Find your booth** on the portal or dial 1950\n"
            "- ✅ **Step 7 — Vote on polling day!** Bring your ID\n\n"
            "> Remember: VoteWise can guide you, but the real registration happens at "
            "[voters.eci.gov.in](https://voters.eci.gov.in) 🏛️\n\n"
            "Which step would you like me to explain?"
        ),
        (
            "**Here are your steps to vote for the first time:**\n\n"
            "1. Check you are 18 and an Indian citizen\n"
            "2. Register using Form 6 on [voters.eci.gov.in](https://voters.eci.gov.in)\n"
            "3. Upload your photo, age proof, and address proof\n"
            "4. Track your application\n"
            "5. Check your name in the voter list\n"
            "6. Find your polling booth\n"
            "7. Vote on the polling day!\n\n"
            "Which one do you want me to explain more?"
        ),
        (
            "**Here is what you need to do, one step at a time:**\n\n"
            "Step 1: Make sure you are 18 years old and an Indian citizen.\n\n"
            "Step 2: Go to [voters.eci.gov.in](https://voters.eci.gov.in) and fill Form 6 to register.\n\n"
            "Step 3: Upload your photo, age proof, and address proof.\n\n"
            "Step 4: After registering, check if your name appears in the voter list.\n\n"
            "Step 5: Find your polling booth on the same portal.\n\n"
            "Step 6: On election day, carry your ID and vote.\n\n"
            "Which step would you like explained?"
        ),
    )
    return _reply(
        answer, "show_path_no_epic", state,
        ["Explain Step 1", "Explain Step 2 — Form 6", "Explain Step 3", "What ID can I carry?"]
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

    answer = _tone(persona,
        (
            "**Great — you already have a Voter ID! Here's what to do next:**\n\n"
            "- **Step 1 — Verify your name** in the Electoral Roll at "
            "[electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n"
            "- **Step 2 — Check your details** — name, photo, constituency, and booth number\n"
            "- **Step 3 — Find your polling booth** on [voters.eci.gov.in](https://voters.eci.gov.in) or call **1950**\n"
            "- **Step 4 — Carry accepted ID on polling day** — your Voter ID, Aadhaar, PAN, or Passport\n"
            "- **Step 5 — Vote using the EVM** — the VVPAT slip confirms your vote\n\n"
            "Which step would you like me to explain?"
        ),
        (
            "**You're almost ready to vote! 🗳️ Just a few things to check:**\n\n"
            "- ✅ **Check your name** at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n"
            "- ✅ **Find your booth** on [voters.eci.gov.in](https://voters.eci.gov.in) or call 1950\n"
            "- ✅ **Carry a valid ID** on polling day (Voter ID, Aadhaar, PAN, or Passport)\n"
            "- ✅ **Vote using the EVM** — a VVPAT slip will confirm your choice\n\n"
            "You're ready! Which step would you like to know more about?"
        ),
        (
            "**You already have a Voter ID — here's your checklist:**\n\n"
            "1. Check your name is in the voter list\n"
            "2. Find your polling booth\n"
            "3. On polling day, carry your ID and go vote!\n\n"
            "What would you like to know more about?"
        ),
        (
            "Good, you have a Voter ID.\n\n"
            "Step 1: Check your name in the voter list at [electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in).\n\n"
            "Step 2: Find your polling booth on [voters.eci.gov.in](https://voters.eci.gov.in).\n\n"
            "Step 3: On polling day, carry your Voter ID or any accepted ID and vote.\n\n"
            "Which step would you like explained?"
        ),
    )
    return _reply(
        answer, "show_path_has_epic", state,
        ["How to check my name", "How to find my booth", "What ID do I carry", "How do I vote on polling day"]
    )


def _turning_18_path(state: dict, persona: str) -> dict:
    """Path for users turning 18 soon."""
    state["flow_type"] = "turning_18"
    state["last_path_steps"] = [
        {"id": "check_eligibility", "title": "Check qualifying date"},
        {"id": "register_form6", "title": "Register online (Form 6)"},
        {"id": "upload_docs", "title": "Prepare documents"}
    ]

    answer = _tone(persona,
        (
            "**You're eligible to register even before you turn 18! Here's what to know:**\n\n"
            "- Form 6 is for new voter registration and is open to citizens who are **18 or turning 18** "
            "on or before the qualifying date (usually January 1 of the relevant year)\n"
            "- Register in advance at [voters.eci.gov.in](https://voters.eci.gov.in)\n"
            "- Prepare your documents: age proof (birth certificate or 10th mark sheet), address proof, and a photo\n"
            "- **Always verify the current eligibility date and deadline** at [eci.gov.in](https://eci.gov.in) "
            "as these change with each election cycle\n\n"
            "> VoteWise cannot confirm your exact eligibility date. Please verify on the official portal."
        ),
        (
            "**So exciting that you'll be voting soon! 🌟**\n\n"
            "Here's the good news: you can register **before** you actually turn 18, "
            "as long as you'll be 18 by the qualifying date (check [eci.gov.in](https://eci.gov.in) for the exact date).\n\n"
            "- Visit [voters.eci.gov.in](https://voters.eci.gov.in) and fill Form 6\n"
            "- Keep your age proof ready (birth certificate or 10th mark sheet)\n"
            "- Check back on the portal to confirm your registration\n\n"
            "> Current deadlines change — always verify at [eci.gov.in](https://eci.gov.in) 🏛️"
        ),
        (
            "**Good news — you can register before you turn 18!**\n\n"
            "If you'll be 18 by the qualifying date, you can fill Form 6 now on [voters.eci.gov.in](https://voters.eci.gov.in).\n\n"
            "Keep your birth certificate or 10th mark sheet ready as age proof.\n\n"
            "Check [eci.gov.in](https://eci.gov.in) for the exact date rules."
        ),
        (
            "You can register soon.\n\n"
            "Visit [voters.eci.gov.in](https://voters.eci.gov.in) and fill Form 6 when you are ready.\n\n"
            "Keep your age proof (birth certificate) and address proof ready.\n\n"
            "For exact dates, check [eci.gov.in](https://eci.gov.in)."
        ),
    )
    return _reply(
        answer, "show_path_turning_18", state,
        ["What documents do I need", "How do I fill Form 6", "What is the qualifying date"]
    )


def _under_18_path(state: dict, persona: str) -> dict:
    """Path for users under 18."""
    answer = _tone(persona,
        (
            "You cannot vote yet — the minimum voting age in India is **18 years**.\n\n"
            "But that doesn't mean you can't learn! VoteWise can teach you:\n"
            "- How elections work\n"
            "- What parties and candidates do\n"
            "- How EVMs and VVPAT work\n"
            "- What the election timeline looks like\n\n"
            "What would you like to learn about?"
        ),
        (
            "You can't vote just yet — India's voting age is **18** — but you're already thinking ahead, which is great! 🌟\n\n"
            "I can help you learn everything about elections so you're fully ready when the time comes.\n\n"
            "What topic interests you?"
        ),
        (
            "You need to be 18 to vote in India. But you can still learn!\n\n"
            "I can explain how elections work, what parties do, what EVM is, and much more.\n\n"
            "What would you like to learn about?"
        ),
        (
            "The voting age in India is 18. You cannot vote yet.\n\n"
            "But I can still teach you how elections work. What would you like to know?"
        ),
    )
    return _reply(
        answer, "show_under_18", state,
        ["How do elections work", "What is EVM", "What is NOTA", "Election timeline"]
    )


def _returning_voter_path(state: dict, persona: str) -> dict:
    """Path for users who have voted before."""
    state["flow_type"] = "returning_voter"
    state["last_path_steps"] = [
        {"id": "check_name", "title": "Check name"},
        {"id": "find_booth", "title": "Find polling booth"},
        {"id": "carry_id", "title": "Carry accepted ID"}
    ]
    answer = _tone(persona,
        (
            "Welcome back! Since you've voted before, here's a quick refresher:\n\n"
            "- **Check your name** in the current Electoral Roll at "
            "[electoralsearch.eci.gov.in](https://electoralsearch.eci.gov.in)\n"
            "- **Find your booth** on [voters.eci.gov.in](https://voters.eci.gov.in)\n"
            "- **Carry valid ID** — Voter ID, Aadhaar, PAN, or Passport\n\n"
            "Is there something specific I can help with?"
        ),
        (
            "Great to hear you've voted before! 🗳️\n\n"
            "Just make sure your name is still in the voter list and your booth is the same.\n\n"
            "Is there something specific you want help with?"
        ),
        (
            "Good, you've voted before! Here's what to check:\n"
            "1. Is your name still in the voter list?\n"
            "2. Has your polling booth changed?\n"
            "3. Do you have a valid ID?\n\n"
            "What do you need help with?"
        ),
        (
            "Good. Since you have voted before, just check your name in the voter list and find your booth.\n\n"
            "What would you like help with?"
        ),
    )
    return _reply(
        answer, "show_returning_voter", state,
        ["Check my name in voter list", "Find my polling booth", "What ID can I carry"]
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
