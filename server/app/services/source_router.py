"""
Source Router — Lightweight intent classifier for VoteWise.
Classifies user messages BEFORE they reach RAG or Gemini,
so that only genuinely civic/political queries use those resources.

Intent categories (checked in priority order):
  1. greeting            → direct answer
  2. assistant_identity  → direct answer
  3. current_date_time   → direct answer (server clock)
  4. unclear_followup    → clarification prompt
  5. political_persuasion_or_attack → safety refusal (redundant with safety_service, kept for meta)
  6. illegal_voting      → safety refusal (redundant with safety_service, kept for meta)
  7. current_election_info → redirect to official sources
  8. civic_static        → RAG + Gemini
  9. political_party_neutral → RAG + Gemini (neutral)
"""
import re
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.utils.logging import get_logger

try:
    from zoneinfo import ZoneInfo
    _APP_TZ = ZoneInfo(settings.APP_TIMEZONE)
except Exception:
    # Fallback: fixed UTC+5:30 offset (IST) when tzdata is unavailable
    _APP_TZ = timezone(timedelta(hours=5, minutes=30))

logger = get_logger("source_router")

# ---------------------------------------------------------------------------
# Intent detection patterns
# ---------------------------------------------------------------------------

# 1. Greeting — short, casual openers
_GREETING_PATTERNS = [
    r"^(hi|hello|hey|namaste|namaskar|hola|howdy|good\s*(morning|afternoon|evening|night)|greetings|sup|yo)\b",
    r"^(hi|hello|hey)\s*[!.,?]*\s*$",
]
_GREETING_RE = [re.compile(p, re.IGNORECASE) for p in _GREETING_PATTERNS]

# 2. Assistant identity
_IDENTITY_PATTERNS = [
    r"(what\s*is\s*your\s*name|who\s*are\s*you|what\s*can\s*you\s*do|what\s*do\s*you\s*do|tell\s*me\s*about\s*yourself|who\s*made\s*you|what\s*are\s*you)",
]
_IDENTITY_RE = [re.compile(p, re.IGNORECASE) for p in _IDENTITY_PATTERNS]

# 3. Current date/time — but NOT election-date queries
_DATE_EXCLUDE = re.compile(r"(election|polling|voting|schedule|phase|result)", re.IGNORECASE)
_DATE_PATTERNS = [
    r"(what\s*(is|'s)\s*(today'?s?|the|current)\s*(date|day|time))",
    r"(today'?s?\s*(date|day|time))",
    r"(what\s*day\s*is\s*it)",
    r"(current\s*(date|day|time))",
    r"(what\s*time\s*is\s*it)",
    r"(aaj\s*(ki|ka)\s*(date|tarikh|din))",
]
_DATE_RE = [re.compile(p, re.IGNORECASE) for p in _DATE_PATTERNS]

# 4. Unclear follow-up — very short, context-dependent messages
_FOLLOWUP_EXACT = {
    "yes", "yeah", "yep", "yup", "ok", "okay", "sure", "go on",
    "continue", "tell me more", "more", "explain", "elaborate",
    "go ahead", "and", "then", "next", "please", "haan", "ha",
    "aur", "aage", "batao",
}

# 7. Current election info — live / temporal queries
_CURRENT_ELECTION_PATTERNS = [
    r"(latest|current|upcoming|next|recent|new|live)\s*(election|result|schedule|phase|date|poll)",
    r"election\s*(schedule|date|result|phase|timeline|update)",
    r"who\s*(is|are)\s*(currently|now)\s*(ruling|governing|in\s*power|pm|chief\s*minister|cm)",
    r"(current|present)\s*(pm|prime\s*minister|chief\s*minister|cm|president|government|ruling)",
    r"(latest|recent)\s*(result|news|update)",
    r"(when\s*(is|are)\s*(the\s*)?(next|upcoming)\s*(election|poll|vote))",
    r"(lok\s*sabha|vidhan\s*sabha|assembly)\s*(election|result|date|schedule)",
]
_CURRENT_ELECTION_RE = [re.compile(p, re.IGNORECASE) for p in _CURRENT_ELECTION_PATTERNS]

# 9. Political party neutral — party info queries (no opinion)
_PARTY_NAMES = r"(bjp|congress|inc|aap|bsp|cpi|npp|tnc|sp|rjd|jdu|tmc|dmk|ysrcp|brs|shiv\s*sena|ncp|jmm|ljp|rld|ssp)"
_PARTY_NEUTRAL_PATTERNS = [
    rf"(what\s*(is|are)|tell\s*me\s*about|explain|describe|history\s*of|about)\s*{_PARTY_NAMES}",
    r"(what\s*(is|are)|tell\s*me\s*about|explain)\s*(national\s*part|regional\s*part|political\s*part|manifesto|party\s*system)",
    r"(list|name)\s*(all\s*)?(national|regional|political)\s*part",
    r"(what\s*is\s*(a\s*)?manifesto)",
]
_PARTY_NEUTRAL_RE = [re.compile(p, re.IGNORECASE) for p in _PARTY_NEUTRAL_PATTERNS]

# 8. Civic static — election education / process queries
_CIVIC_KEYWORDS = [
    "register to vote", "voter registration", "voter id", "epic card",
    "evm", "vvpat", "nota", "polling", "poll booth", "ballot",
    "counting", "voter list", "electoral roll", "election commission",
    "model code of conduct", "mcc", "nomination", "candidate",
    "constituency", "booth", "first time voter", "postal ballot",
    "absentee", "overseas voter", "nri voter", "pwd voter",
    "senior citizen voter", "form 6", "form 7", "form 8",
    "voter helpline", "1950", "voters.eci.gov.in",
    "how to vote", "how do i vote", "voting process", "voting age",
    "election process", "democracy", "eci",
]

# 5. Voter registration — high-confidence registration queries (direct answer, no RAG noise)
_VOTER_REG_PATTERNS = [
    r"(how\s*(do|can|to)\s*(i|we|one)\s*(register|enroll|sign\s*up)\s*(to\s*vote|as\s*(a\s*)?voter|for\s*voting|on\s*(the\s*)?voter))",
    r"(how\s*to\s*(apply|get|obtain)\s*(for\s*)?(voter\s*id|epic\s*card|voter\s*card|voter\s*id\s*card))",
    r"(apply\s*(for\s*)?(voter\s*id|epic\s*card|voter\s*registration))",
    r"(register\s*(myself|me|as\s*(a\s*)?voter))",
    r"(new\s*voter\s*registration|first\s*time\s*voter\s*registration)",
    r"(form\s*6\s*(voter|registration|apply|fill))",
    r"(voter\s*registration\s*(process|steps?|procedure|online|how))",
    r"(how\s*do\s*i\s*(become|get\s*registered\s*as)\s*(a\s*)?voter)",
    r"(i\s*am\s*\d+.*register\s*(to\s*vote|as\s*(a\s*)?voter))",
]
_VOTER_REG_RE = [re.compile(p, re.IGNORECASE) for p in _VOTER_REG_PATTERNS]

# 10. EVM / VVPAT — what it is and how it works
_EVM_PATTERNS = [
    r"\b(what\s*is|explain|how\s*does|describe|tell\s*me\s*about|about)\s*(an?\s*)?(evm|electronic\s*voting\s*machine)\b",
    r"\b(what\s*is|explain|how\s*does|describe|tell\s*me\s*about|about)\s*(an?\s*)?vvpat\b",
    r"\bevm\s*(and|or|&)\s*vvpat\b",
    r"\bvvpat\s*(and|or|&)\s*evm\b",
    r"\bevm\s*(work|works|function|machine|voting)\b",
    r"\belectronic\s*voting\s*machine\b",
]
_EVM_RE = [re.compile(p, re.IGNORECASE) for p in _EVM_PATTERNS]

# 11. NOTA — None of the Above
_NOTA_PATTERNS = [
    r"\b(what\s*is|explain|tell\s*me\s*about|about|describe)\s*nota\b",
    r"\bnone\s*of\s*the\s*above\b",
]
_NOTA_RE = [re.compile(p, re.IGNORECASE) for p in _NOTA_PATTERNS]

# 12. Coalition government
_COALITION_PATTERNS = [
    r"\b(what\s*is|explain|tell\s*me\s*about|about|describe)\s*(a?\s*)?coalition(\s*government)?\b",
    r"\bcoalition\s*(government|politics|rule|ministry)\b",
    r"\bno\s*(single\s*)?party\s*(gets?|has|wins?)\s*(a?\s*)?majority\b",
    r"\bhung\s*(parliament|house|assembly)\b",
]
_COALITION_RE = [re.compile(p, re.IGNORECASE) for p in _COALITION_PATTERNS]

# 13. Polling day — what happens on voting day
_POLLING_DAY_PATTERNS = [
    r"\b(explain|what\s*happens?|describe|how\s*to\s*vote)\s*(on\s*)?(polling|voting)\s*day\b",
    r"\bpolling\s*(day|booth|station|process|procedure)\b",
    r"\bwhat\s*happens?\s*(at|in)\s*(the\s*)?(poll(ing)?\s*booth|voting\s*booth|polling\s*station)\b",
    r"\bvoting\s*(process|procedure|step|day)\b",
]
_POLLING_DAY_RE = [re.compile(p, re.IGNORECASE) for p in _POLLING_DAY_PATTERNS]

# 14. Voter list / electoral roll check
_VOTER_LIST_PATTERNS = [
    r"\b(how\s*(do|can|to)\s*(i|we|one)\s*)?(check|find|search|verify|look\s*up)\s*(my\s*)?name\s*(in|on)\s*(the\s*)?(voter|electoral)\s*(list|roll)\b",
    r"\b(check|find|search|verify)\s*(my\s*)?(voter\s*list|electoral\s*roll)\b",
    r"\b(find|check|locate)\s*(my\s*)?(polling\s*(booth|station)|booth\s*number)\b",
    r"\belectoral\s*roll\b",
    r"\bam\s*i\s*(registered|enrolled|in\s*(the\s*)?voter\s*list)\b",
]
_VOTER_LIST_RE = [re.compile(p, re.IGNORECASE) for p in _VOTER_LIST_PATTERNS]

# ---------------------------------------------------------------------------
# Direct response builders
# ---------------------------------------------------------------------------

IDENTITY_RESPONSE = (
    "I'm VoteWise, a neutral civic education assistant that helps people "
    "understand Indian elections, voting steps, timelines, and democracy basics."
)

FOLLOWUP_CLARIFICATION = (
    "Sure — what would you like me to explain: voter registration, "
    "polling day, EVM/VVPAT, election timeline, or politics basics?"
)

CURRENT_ELECTION_REDIRECT = (
    "I don't have access to live election data right now. "
    "For the latest official election schedule, results, and notifications, "
    "please visit:\n\n"
    "• **Election Commission of India**: [eci.gov.in](https://eci.gov.in)\n"
    "• **Voter Services**: [voters.eci.gov.in](https://voters.eci.gov.in)\n"
    "• **ECI Results**: [results.eci.gov.in](https://results.eci.gov.in)\n\n"
    "I can help you understand the election process, voter registration, "
    "or how EVMs work — just ask!"
)

VOTER_REGISTRATION_RESPONSE = (
    "**How to Register as a Voter in India**\n\n"
    "**Eligibility**\n"
    "- Indian citizen\n"
    "- 18 years or older on the qualifying date (usually January 1 of the reference year)\n"
    "- Ordinarily resident in the constituency where you want to register\n\n"
    "**Step-by-step registration**\n"
    "1. Visit **[voters.eci.gov.in](https://voters.eci.gov.in)** (official ECI Voter Portal)\n"
    "2. Click **New Voter Registration** and select **Form 6**\n"
    "3. Fill in your personal details (name, date of birth, address, mobile)\n"
    "4. Upload supporting documents if prompted (proof of age, proof of address)\n"
    "5. Submit the application online — you will receive an acknowledgement number\n"
    "6. Track your application status at voters.eci.gov.in using the acknowledgement number\n"
    "7. After approval, verify your name appears in the **electoral roll / voter list**\n"
    "8. Download or collect your **Voter ID (EPIC card)** from the BLO (Booth Level Officer) or via the portal\n\n"
    "**On polling day**, carry your Voter ID or any of the 12 approved alternate photo IDs.\n\n"
    "For official guidance: [eci.gov.in](https://eci.gov.in) | [voters.eci.gov.in](https://voters.eci.gov.in)"
)

EVM_VVPAT_RESPONSE = (
    "**EVM and VVPAT — How Voting Works in India**\n\n"
    "**EVM (Electronic Voting Machine)**\n"
    "- An EVM is an electronic device used to record votes in Indian elections.\n"
    "- On the ballot unit, each candidate's name, party symbol, and a blue button are displayed.\n"
    "- The voter presses the button next to their chosen candidate's name and symbol.\n"
    "- A beep sound and a red light confirm the vote has been recorded.\n\n"
    "**VVPAT (Voter Verifiable Paper Audit Trail)**\n"
    "- VVPAT is a device attached to the EVM that provides a paper confirmation.\n"
    "- After a voter presses the button, a printed slip showing the candidate's name and symbol \n"
    "  is visible through a small glass window for **7 seconds**.\n"
    "- This slip then drops into a sealed box inside the VVPAT — the voter does **not** take it.\n"
    "- It lets voters confirm their vote was recorded as intended.\n\n"
    "For official details: [eci.gov.in](https://eci.gov.in)"
)

NOTA_RESPONSE = (
    "**NOTA — None of the Above**\n\n"
    "- **NOTA** stands for **None of the Above**.\n"
    "- It is a voting option available on the EVM (Electronic Voting Machine) at the end of the candidate list.\n"
    "- Choosing NOTA means the voter does not prefer any of the listed candidates.\n"
    "- NOTA votes are counted and reported, but they do not help any candidate win.\n"
    "- It was introduced by the Supreme Court of India in 2013 to give voters a way to reject all candidates.\n\n"
    "NOTA does not invalidate the election — the candidate with the most votes still wins.\n\n"
    "For official details: [eci.gov.in](https://eci.gov.in)"
)

COALITION_RESPONSE = (
    "**Coalition Government — What It Means**\n\n"
    "- A **coalition government** is formed when **two or more political parties** join together \n"
    "  to collectively hold a majority of seats in the legislature.\n"
    "- It typically happens when **no single party wins a clear majority** on its own \n"
    "  (more than half of all seats).\n"
    "- The parties in a coalition agree on a common agenda and share ministerial positions.\n"
    "- A legislature where no party has a majority is often called a **hung parliament** or \n"
    "  **hung assembly**.\n\n"
    "Coalition governments are common in India's multi-party democratic system.\n\n"
    "For more on Indian democracy: [eci.gov.in](https://eci.gov.in)"
)

POLLING_DAY_RESPONSE = (
    "**What Happens on Polling Day**\n\n"
    "1. **Go to your assigned polling station** — check your booth number on [voters.eci.gov.in](https://voters.eci.gov.in) before election day.\n"
    "2. **Carry a valid photo ID** — Voter ID (EPIC card) or any of the 12 approved alternate photo IDs (Aadhaar, passport, PAN card, etc.).\n"
    "3. **Join the queue** at the correct booth for your name in the voter list.\n"
    "4. **Show your ID** to polling officials — they verify your name in the voter list.\n"
    "5. **Get an ink mark** on your left index finger (indelible ink that lasts several days).\n"
    "6. **Enter the voting compartment** — it is private, no one can see your vote.\n"
    "7. **Press the button** next to your chosen candidate's name/symbol on the EVM.\n"
    "8. **Check the VVPAT slip** — it appears behind a glass window for 7 seconds, showing your choice.\n"
    "9. **Leave the polling station peacefully** after voting.\n\n"
    "For official guidelines: [eci.gov.in](https://eci.gov.in)"
)

VOTER_LIST_RESPONSE = (
    "**How to Check Your Name in the Voter List**\n\n"
    "1. Visit **[voters.eci.gov.in](https://voters.eci.gov.in)** — the official ECI Voter Services Portal.\n"
    "2. Click **\"Search in Electoral Roll\"** and enter your name, date of birth, and state/district.\n"
    "3. You can also search by **EPIC number** (Voter ID card number) for a direct match.\n"
    "4. Your polling station (booth name and address) will be shown once your name is found.\n"
    "5. If your name is missing, you can **apply for inclusion** using Form 6 on the same portal.\n\n"
    "VoteWise cannot directly verify your voter status — please use the official portal only.\n\n"
    "Official portal: [voters.eci.gov.in](https://voters.eci.gov.in)"
)


def _safe_now() -> datetime:
    """Return current datetime in the configured timezone (safe fallback)."""
    return datetime.now(_APP_TZ)


def _get_greeting() -> str:
    """Return a friendly greeting with the current IST time of day."""
    hour = _safe_now().hour
    if hour < 12:
        period = "morning"
    elif hour < 17:
        period = "afternoon"
    else:
        period = "evening"
    return (
        f"Good {period}! I'm VoteWise, your civic education assistant. "
        "I can help you with voter registration, election processes, EVMs, "
        "and democracy basics in India. What would you like to know?"
    )


def _get_date_response() -> str:
    """Return the current date/time in IST."""
    now = _safe_now()
    return (
        f"Today is **{now.strftime('%A, %d %B %Y')}** "
        f"and the current time is **{now.strftime('%I:%M %p')} IST**."
    )


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------

def classify_intent(message: str, context: str | None = None) -> dict:
    """
    Classify a user message into one of the intent categories.

    Returns:
        {
            "intent": str,           # intent category name
            "direct_response": str | None,  # if set, return this directly (no RAG/Gemini)
            "use_rag": bool,         # whether to use RAG retrieval
            "use_model": bool,       # whether to call Gemini
        }
    """
    cleaned = message.strip()
    lower = cleaned.lower()

    # --- 1. Greeting ---
    if len(cleaned.split()) <= 5:
        for pat in _GREETING_RE:
            if pat.search(lower):
                logger.info(f"Intent: greeting | msg='{cleaned[:40]}'")
                return {
                    "intent": "greeting",
                    "direct_response": _get_greeting(),
                    "use_rag": False,
                    "use_model": False,
                }

    # --- 2. Assistant identity ---
    for pat in _IDENTITY_RE:
        if pat.search(lower):
            logger.info(f"Intent: assistant_identity | msg='{cleaned[:40]}'")
            return {
                "intent": "assistant_identity",
                "direct_response": IDENTITY_RESPONSE,
                "use_rag": False,
                "use_model": False,
            }

    # --- 3. Current date/time (exclude election-date queries) ---
    if not _DATE_EXCLUDE.search(lower):
        for pat in _DATE_RE:
            if pat.search(lower):
                logger.info(f"Intent: current_date_time | msg='{cleaned[:40]}'")
                return {
                    "intent": "current_date_time",
                    "direct_response": _get_date_response(),
                    "use_rag": False,
                    "use_model": False,
                }

    # --- 4. Unclear follow-up ---
    if lower in _FOLLOWUP_EXACT or (len(cleaned.split()) <= 3 and lower.rstrip("?.!,") in _FOLLOWUP_EXACT):
        has_context = bool(context and context.strip())
        if not has_context:
            logger.info(f"Intent: unclear_followup (no context) | msg='{cleaned[:40]}'")
            return {
                "intent": "unclear_followup",
                "direct_response": FOLLOWUP_CLARIFICATION,
                "use_rag": False,
                "use_model": False,
            }
        else:
            # Has context — let it pass through to RAG/Gemini with the context
            logger.info(f"Intent: unclear_followup (has context, passing through) | msg='{cleaned[:40]}'")
            return {
                "intent": "unclear_followup",
                "direct_response": None,
                "use_rag": True,
                "use_model": True,
            }

    # --- 7. Current election info ---
    for pat in _CURRENT_ELECTION_RE:
        if pat.search(lower):
            if settings.ENABLE_GOOGLE_SEARCH_GROUNDING:
                # Let it pass through to Gemini with search grounding
                logger.info(f"Intent: current_election_info (search enabled) | msg='{cleaned[:40]}'")
                return {
                    "intent": "current_election_info",
                    "direct_response": None,
                    "use_rag": True,
                    "use_model": True,
                }
            else:
                logger.info(f"Intent: current_election_info (search disabled → redirect) | msg='{cleaned[:40]}'")
                return {
                    "intent": "current_election_info",
                    "direct_response": CURRENT_ELECTION_REDIRECT,
                    "use_rag": False,
                    "use_model": False,
                }

    # --- 9. Political party neutral ---
    for pat in _PARTY_NEUTRAL_RE:
        if pat.search(lower):
            logger.info(f"Intent: political_party_neutral | msg='{cleaned[:40]}'")
            return {
                "intent": "political_party_neutral",
                "direct_response": None,
                "use_rag": True,
                "use_model": True,
            }

    # --- 5. Voter registration (direct answer — deterministic, no RAG noise) ---
    for pat in _VOTER_REG_RE:
        if pat.search(lower):
            logger.info(f"Intent: voter_registration | msg='{cleaned[:40]}'")
            return {
                "intent": "voter_registration",
                "direct_response": VOTER_REGISTRATION_RESPONSE,
                "use_rag": False,
                "use_model": False,
            }

    # --- 10. EVM / VVPAT ---
    for pat in _EVM_RE:
        if pat.search(lower):
            logger.info(f"Intent: evm_vvpat | msg='{cleaned[:40]}'")
            return {
                "intent": "evm_vvpat",
                "direct_response": EVM_VVPAT_RESPONSE,
                "use_rag": False,
                "use_model": False,
            }

    # --- 11. NOTA ---
    for pat in _NOTA_RE:
        if pat.search(lower):
            logger.info(f"Intent: nota | msg='{cleaned[:40]}'")
            return {
                "intent": "nota",
                "direct_response": NOTA_RESPONSE,
                "use_rag": False,
                "use_model": False,
            }

    # --- 12. Coalition government ---
    for pat in _COALITION_RE:
        if pat.search(lower):
            logger.info(f"Intent: coalition_government | msg='{cleaned[:40]}'")
            return {
                "intent": "coalition_government",
                "direct_response": COALITION_RESPONSE,
                "use_rag": False,
                "use_model": False,
            }

    # --- 13. Polling day ---
    for pat in _POLLING_DAY_RE:
        if pat.search(lower):
            logger.info(f"Intent: polling_day | msg='{cleaned[:40]}'")
            return {
                "intent": "polling_day",
                "direct_response": POLLING_DAY_RESPONSE,
                "use_rag": False,
                "use_model": False,
            }

    # --- 14. Voter list / electoral roll check ---
    for pat in _VOTER_LIST_RE:
        if pat.search(lower):
            logger.info(f"Intent: voter_list_check | msg='{cleaned[:40]}'")
            return {
                "intent": "voter_list_check",
                "direct_response": VOTER_LIST_RESPONSE,
                "use_rag": False,
                "use_model": False,
            }

    # --- 8. Civic static (keyword match) ---
    for keyword in _CIVIC_KEYWORDS:
        if keyword in lower:
            logger.info(f"Intent: civic_static (keyword='{keyword}') | msg='{cleaned[:40]}'")
            return {
                "intent": "civic_static",
                "direct_response": None,
                "use_rag": True,
                "use_model": True,
            }

    # --- Default: treat as civic_static (pass to RAG + Gemini) ---
    logger.info(f"Intent: civic_static (default) | msg='{cleaned[:40]}'")
    return {
        "intent": "civic_static",
        "direct_response": None,
        "use_rag": True,
        "use_model": True,
    }
