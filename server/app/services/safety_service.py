"""
Safety Service — Pre-screens messages before sending to Gemini.
Detects and blocks partisan, illegal, or harmful requests.
"""
import re
from app.utils.logging import get_logger

logger = get_logger("safety_service")

# Patterns that should be blocked immediately
BLOCK_PATTERNS = [
    # Party recommendation / persuasion
    r"which party should i vote",
    r"who should i vote for",
    r"best party",
    r"worst party",
    r"(bjp|congress|aap|bsp|cpi|npp|tnc|inc|sp|bsp|rjd|jdu|tmc|dmk|ysrcp|brs|shiv sena).*(good|bad|better|worse|best|worst|great|terrible|corrupt|clean|honest|dishonest)",
    r"(good|bad|better|worse|best|worst|great|terrible|corrupt|clean|honest|dishonest).*(bjp|congress|aap|bsp|cpi|npp|tnc|inc|sp|bsp|rjd|jdu|tmc|dmk|ysrcp|brs|shiv sena)",
    r"convince me to vote",
    r"should i vote for",
    r"vote for (bjp|congress|aap|bsp|cpi|npp|inc)",
    r"vote against (bjp|congress|aap|bsp|cpi|npp|inc)",
    r"write.*propaganda",
    r"write.*campaign.*material",
    r"negative.*campaign",
    r"attack.*party",
    # Illegal activities
    r"fake voter id",
    r"fake voter card",
    r"fake.*voter",
    r"how to vote (twice|multiple|again|more than once)",
    r"vote multiple times",
    r"manipulate.*evm",
    r"hack.*evm",
    r"tamper.*evm",
    r"impersonat.*(election|officer|official|voter)",
    r"pretend.*election official",
    # Hate speech
    r"(hate|kill|destroy|eliminate).*(party|politician|voter|community|religion|caste|hindu|muslim|christian|dalit|brahmin)",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BLOCK_PATTERNS]

SAFE_REFUSAL = (
    "I can help you understand elections and political concepts, but I cannot influence your vote, "
    "promote or attack any party, or assist with illegal activity. Your vote is private and independent. "
    "For official information, visit eci.gov.in or voters.eci.gov.in."
)

_SAFE_REFUSAL_BY_PERSONA: dict[str, str] = {
    "general": SAFE_REFUSAL,
    "first-time-voter": (
        "VoteWise cannot recommend which party or candidate to vote for — your vote is entirely your own choice. "
        "I can explain how elections work, but who you vote for is completely up to you. "
        "For official information, visit voters.eci.gov.in."
    ),
    "student": (
        "That's a tricky question! VoteWise is like a neutral teacher — I explain how elections work, "
        "but I don't tell anyone which party is good or bad. That decision belongs to you when you vote! "
        "For official information, visit eci.gov.in."
    ),
    "elderly": (
        "I am sorry. I cannot help with this. "
        "VoteWise does not support or oppose any party. "
        "Your vote is private. Please visit eci.gov.in for official information."
    ),
}


def check_message(message: str, persona: str = "general") -> dict:
    """
    Returns {"safe": True} if message is safe to process.
    Returns {"safe": False, "reason": "...", "response": "..."} if blocked.

    The refusal wording is adjusted for the persona (elderly/student get simpler text).
    """
    for pattern in COMPILED_PATTERNS:
        if pattern.search(message):
            logger.warning(f"Safety block triggered | pattern='{pattern.pattern[:40]}...' | persona={persona}")
            refusal = _SAFE_REFUSAL_BY_PERSONA.get(persona, SAFE_REFUSAL)
            return {
                "safe": False,
                "reason": "Request violates VoteWise neutrality policy.",
                "response": refusal,
            }
    return {"safe": True}
