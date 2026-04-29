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
