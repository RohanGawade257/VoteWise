"""
Gemini Service — Handles all Google Gemini API calls.
Uses google-genai SDK. Never logs or exposes the API key.
"""
import asyncio
from functools import partial
from google import genai
from google.genai import types
from urllib.parse import urlparse
from datetime import datetime, timezone
from app.config import settings
from app.prompts.system_prompt import SYSTEM_PROMPT, build_persona_instruction
from app.services import rag_service
from app.services.rag_service import get_confidence, is_in_civic_scope
from app.utils.logging import get_logger
from app.models import ChatResponse, SourceItem, SafetyInfo, MetaInfo

logger = get_logger("gemini_service")

def _is_official_source(url: str, intent: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
            
        if intent == "current_election_info":
            if domain in ("eci.gov.in", "voters.eci.gov.in", "electoralsearch.eci.gov.in"):
                return True
            if "ceo" in domain and ("nic.in" in domain or "gov.in" in domain):
                return True
            if "sec" in domain and ("nic.in" in domain or "gov.in" in domain):
                return True
            return False
            
        elif intent == "current_party_info":
            party_domains = ["bjp.org", "inc.in", "aamaadmiparty.org", "aitcofficial.org", "samajwadiparty.in"]
            if any(p in domain for p in party_domains):
                return True
            if "gov.in" in domain or "nic.in" in domain or "sansad.in" in domain:
                return True
            return False
            
        elif intent == "current_public_info":
            allowed_domains = ["india.gov.in", "pib.gov.in", "pmindia.gov.in", "presidentofindia.gov.in", "eci.gov.in", "sansad.in"]
            if domain in allowed_domains or domain.endswith(".gov.in") or domain.endswith(".nic.in"):
                return True
            return False
    except Exception:
        return False
    return False

# Error messages that are safe to show to frontend users
ERROR_MESSAGES = {
    "no_key":     "AI backend is not configured yet. Please contact the administrator.",
    "auth":       "AI service authentication failed. Please contact the administrator.",
    "quota":      "AI service quota or rate limit reached. Please try again later.",
    "overload":   "AI service is temporarily overloaded. Please try again in a moment.",
    "timeout":    "AI service request timed out. Please try again.",
    "unknown":    "AI service failed unexpectedly. Please try again.",
}

async def generate_chat_response(
    message: str,
    persona: str,
    context: str | None,
    intent: str,
    use_rag: bool = True
) -> ChatResponse:

    # --- 1. Check API key ---
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is missing from environment.")
        raise ValueError(ERROR_MESSAGES["no_key"])

    # --- 2. Out-of-scope guard (before RAG / before Gemini) ---
    # If the query has zero civic keywords AND use_rag is True (civic flow),
    # return a focused scope message without touching Gemini.
    if use_rag and not is_in_civic_scope(f"{context or ''} {message}"):
        logger.info(f"Out-of-scope query detected | persona={persona} | msg='{message[:50]}'")
        scope_msg = (
            "VoteWise focuses on Indian elections, voter registration, and civic education. "
            "I'm not able to help with that topic, but I'd be happy to answer any questions "
            "about voting, EVMs, election timelines, or how to register as a voter. "
            "What would you like to know?"
        )
        return ChatResponse(
            answer=scope_msg,
            sources=[],
            safety=SafetyInfo(blocked=False, reason=None),
            meta=MetaInfo(
                model="scope-guard",
                used_rag=False,
                used_search_grounding=False,
                intent=intent,
                used_direct_answer=True,
                used_model=False,
                rag_confidence="none",
                rag_chunks_used=0,
                source_files_used=[],
            )
        )

    # --- 3. RAG retrieval (capped at 3 chunks) ---
    rag_chunks: list = []
    rag_context_block = ""
    used_rag = False
    rag_confidence = "none"
    source_files: list[str] = []

    if use_rag:
        rag_query = f"{context or ''} {message}".strip()
        rag_chunks = rag_service.retrieve(rag_query, top_k=3)   # hard cap at 3
        rag_context_block = rag_service.format_for_prompt(rag_chunks)
        used_rag = bool(rag_chunks)
        if rag_chunks:
            rag_confidence = rag_chunks[0].get("confidence", get_confidence(rag_chunks[0]["score"]))
            source_files = list(dict.fromkeys(c["source_file"] for c in rag_chunks))

    # --- 4. Build the full prompt ---
    persona_instruction = build_persona_instruction(persona)
    parts = [
        f"PERSONA INSTRUCTION: {persona_instruction}",
    ]

    # Confidence-aware prompt instruction
    if use_rag:
        if rag_confidence == "high":
            parts.append(
                "CONFIDENCE: The knowledge base has a strong match for this question. "
                "Answer confidently using the context below. Keep the answer under 180 words. "
                "Use bullet points for steps. No long paragraphs."
            )
        elif rag_confidence == "medium":
            parts.append(
                "CONFIDENCE: The knowledge base has a partial match. "
                "Answer using the context, but add a brief note if anything might need verification. "
                "Keep the answer under 150 words. Use bullets for steps."
            )
        elif rag_confidence == "low":
            parts.append(
                "CONFIDENCE: The knowledge base match is weak. "
                "If you cannot answer confidently from the context, ask the user a clarifying question instead of guessing. "
                "Keep any answer under 120 words."
            )
        else:
            # rag_confidence == 'none' but use_rag=True and civic scope passed
            parts.append(
                "CONFIDENCE: No specific knowledge base match found. "
                "Answer from general civic knowledge if you are confident, otherwise politely ask the user to rephrase. "
                "Keep response under 120 words."
            )
    else:
        parts.append("Keep your answer under 180 words. Use bullet points for multi-step answers.")
    if context:
        parts.append(f"PAGE CONTEXT: The user is currently on the page: {context}")
        
    if intent == "current_election_info":
        parts.append(
            "You are VoteWise. The user is asking for live/current election information. Use Google Search grounding and rely only on official election sources. Prefer eci.gov.in, voters.eci.gov.in, electoralsearch.eci.gov.in, official state CEO websites, and official State Election Commission websites. If you cannot verify from an official source, say you cannot verify it and direct the user to official portals. Do not guess. Do not use old model knowledge."
        )
    elif intent == "current_party_info":
        parts.append(
            "You are VoteWise. The user is asking for current party leadership or current party profile information. Use Google Search grounding and rely only on official party websites or official government/parliament sources. Do not use campaign propaganda, news gossip, social media posts, blogs, or Wikipedia as primary source. Do not praise or criticize any party. If official verification is missing, return a safe fallback."
        )
    elif intent == "current_public_info":
        parts.append(
            "You are VoteWise. The user is asking for current public office or current government information. Use Google Search grounding and rely only on official government sources such as india.gov.in, pib.gov.in, official ministry websites, official state government websites, eci.gov.in for election offices, and nic.in/gov.in domains. If official verification is missing, return a safe fallback. Do not guess."
        )
        
    if rag_context_block:
        parts.append(rag_context_block)
    parts.append(f"USER QUESTION: {message}")
    full_user_prompt = "\n\n".join(parts)

    # --- 5. Build source list ---
    sources = []
    seen_urls: set = set()
    for chunk in rag_chunks:
        if chunk["source_url"] not in seen_urls:
            sources.append(SourceItem(
                title=chunk["source_title"],
                url=chunk["source_url"],
                type=chunk["source_type"]
            ))
            seen_urls.add(chunk["source_url"])

    # Always include ECI as a base source
    if "https://eci.gov.in" not in seen_urls:
        sources.append(SourceItem(title="Election Commission of India", url="https://eci.gov.in", type="official"))

    # --- 6. Call Gemini ---
    logger.info(f"Calling Gemini | model={settings.GEMINI_MODEL} | persona={persona} | rag_chunks={len(rag_chunks)} | rag_confidence={rag_confidence} | intent={intent}")

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.35,      # slightly lower = more factual
            max_output_tokens=600, # ~180 words; encourages conciseness
        )

        # Optional: Google Search grounding for current info
        used_search = False
        if intent in ("current_election_info", "current_party_info", "current_public_info") and settings.ENABLE_GOOGLE_SEARCH_GROUNDING:
            config.tools = [types.Tool(google_search=types.GoogleSearch())]
            used_search = True
            logger.info(f"Google Search grounding ENABLED for intent: {intent}")

        # The Gemini SDK is synchronous/blocking — run in a thread executor
        # so we don't block FastAPI's async event loop.
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=full_user_prompt,
                config=config,
            )
        )

        answer_text = response.text
        if not answer_text:
            raise ValueError("Empty response from Gemini.")

        # Extract grounding citations if search was used
        found_official_grounding = False
        if used_search and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                    for gc in gm.grounding_chunks[:3]:
                        if hasattr(gc, 'web') and gc.web:
                            url = gc.web.uri
                            title = gc.web.title or "Web Source"
                            sources.append(SourceItem(title=title, url=url, type="web"))
                            if _is_official_source(url, intent):
                                found_official_grounding = True

        checked_at = None
        source_type = None

        if used_search:
            if not found_official_grounding:
                logger.warning(f"Grounding returned no valid official sources for {intent}. Fallback triggered.")
                answer_text = (
                    "I could not verify this from an official source right now. "
                    "Please check [eci.gov.in](https://eci.gov.in) or [voters.eci.gov.in](https://voters.eci.gov.in) "
                    "for the latest official information."
                )
                # Clear unsafe sources, just provide ECI base
                sources = [SourceItem(title="Election Commission of India", url="https://eci.gov.in", type="official")]
                checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                source_type = "unverified_fallback"
            else:
                checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                source_type = "official_grounding"

        logger.info(f"Gemini response OK | length={len(answer_text)} chars | search_grounded={used_search} | official_src={found_official_grounding}")

        final_model_name = "gemini-grounded" if used_search and found_official_grounding else settings.GEMINI_MODEL

        return ChatResponse(
            answer=answer_text,
            sources=sources,
            safety=SafetyInfo(blocked=False, reason=None),
            meta=MetaInfo(
                model=final_model_name,
                used_rag=used_rag,
                used_search_grounding=used_search,
                intent=intent,
                used_direct_answer=False,
                used_model=True,
                rag_confidence=rag_confidence,
                rag_chunks_used=len(rag_chunks),
                source_files_used=source_files,
                checkedAt=checked_at,
                sourceType=source_type
            )
        )

    except Exception as e:
        error_str = str(e)
        status_code = getattr(e, 'status_code', None) or getattr(e, 'code', None)

        # ── Structured diagnostic log (backend-only, never exposed to frontend) ──
        is_quota = (
            status_code == 429
            or "quota" in error_str.lower()
            or "rate" in error_str.lower()
            or "resource_exhausted" in error_str.lower()
        )
        logger.error(
            f"Gemini call FAILED"
            f" | exc_class={type(e).__name__}"
            f" | status_code={status_code}"
            f" | is_quota_or_rate_limit={is_quota}"
            f" | grounding_requested={used_search}"
            f" | intent={intent}"
            f" | msg={error_str[:200]}"
        )

        if "API_KEY" in error_str.upper() or status_code in (401, 403):
            raise PermissionError(ERROR_MESSAGES["auth"])
        if is_quota:
            raise ConnectionError(ERROR_MESSAGES["quota"])
        if status_code == 503 or "overload" in error_str.lower() or "unavailable" in error_str.lower():
            raise ConnectionError(ERROR_MESSAGES["overload"])
        if "timeout" in error_str.lower():
            raise TimeoutError(ERROR_MESSAGES["timeout"])

        raise RuntimeError(ERROR_MESSAGES["unknown"])
