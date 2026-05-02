"""
LLM Classifier Service
Uses Gemini to strictly classify intents before RAG/Orchestration.
This guarantees high-precision classification for definitions and procedures.
"""
import asyncio
import json
from functools import partial
from google import genai
from google.genai import types
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("llm_classifier")

SYSTEM_PROMPT = """
You are the strict intent classification engine for VoteWise, an Indian civic education assistant.
Your job is to analyze the user's message and classify it exactly according to the schema below.
Output raw JSON only.

## Domains:
- registration: about registering to vote, form 6, age, eligibility
- definition: asking what a specific term or concept is
- procedural: asking how to do something (e.g., how to use EVM)
- polling_day: about what happens on the day of voting
- safety: political persuasion, illegal activities, or off-topic

## Intent Types:
- definition: "what is X", "define X"
- how_to: "how do I X", "steps for X"
- yes_no: "can I X", "is it Y"
- general: open-ended or broad queries

## Specific Intents (Map to these if exact match, otherwise use 'general'):
- what_is_voting
- what_is_candidate
- what_is_constituency
- what_is_opposition
- what_is_parliament
- what_is_lok_sabha
- what_is_vidhan_sabha
- how_to_use_evm
- what_is_vvpat
- what_id_to_carry
- can_i_use_aadhaar
- forgot_voter_id
- polling_staff_influence
- vote_secrecy
- evm_wrong_button
- vote_twice
- double_voter_list
- double_voting
- fake_voter_id
- who_can_fill_form_6
- online_registration

## Confidence:
- high: The user's query exactly matches one of the specific intents or intent types.
- low: Ambiguous or generic query.

Output JSON format:
{
    "domain": "...",
    "intent_type": "...",
    "specific_intent": "...",
    "confidence": "high|low"
}
"""

import re

async def classify_intent_with_llm(message: str) -> dict:
    message_lower = message.lower().strip()
    
    # HEURISTIC FAST-PATH (saves API quota)
    heuristics = {
        r"what is voting": "what_is_voting",
        r"what is a candidate": "what_is_candidate",
        r"what is a constituency": "what_is_constituency",
        r"what is opposition": "what_is_opposition",
        r"what is parliament": "what_is_parliament",
        r"what is lok sabha": "what_is_lok_sabha",
        r"what is vidhan sabha": "what_is_vidhan_sabha",
        r"how do i use evm": "how_to_use_evm",
        r"what is vvpat": "what_is_vvpat",
        r"what id do i carry": "what_id_to_carry",
        r"aadhaar": "can_i_use_aadhaar",
        r"forgot.*voter id": "forgot_voter_id",
        r"secret": "vote_secrecy",
        r"wrong button": "evm_wrong_button",
        r"vote twice": "vote_twice",
        r"two voter lists": "double_voter_list",
        r"two places": "double_voting",
        r"fake voter id": "fake_voter_id",
        r"who can fill form 6": "who_can_fill_form_6",
        r"register online": "online_registration",
    }
    
    for pattern, intent_name in heuristics.items():
        if re.search(pattern, message_lower):
            return {
                "domain": "definition",
                "intent_type": "definition" if "what" in pattern else "how_to",
                "specific_intent": intent_name,
                "confidence": "high"
            }

    if not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY. Defaulting classifier to low confidence.")
        return {"domain": "general", "intent_type": "general", "specific_intent": "general", "confidence": "low"}
        
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0
        )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=message,
                config=config,
            )
        )
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        data = json.loads(text)
        logger.info(f"LLM Classification: {data} for msg: '{message[:50]}'")
        return data
        
    except Exception as e:
        logger.error(f"LLM Classifier failed: {e}")
        return {"domain": "general", "intent_type": "general", "specific_intent": "general", "confidence": "low"}
