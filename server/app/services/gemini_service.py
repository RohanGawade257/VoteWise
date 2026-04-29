"""
Gemini Service — Handles all Google Gemini API calls.
Uses google-genai SDK. Never logs or exposes the API key.
"""
from google import genai
from google.genai import types
from urllib.parse import urlparse
from datetime import datetime, timezone
from app.config import settings
from app.prompts.system_prompt import SYSTEM_PROMPT, build_persona_instruction
from app.services import rag_service
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

    # --- 2. RAG retrieval ---
    rag_chunks = []
    rag_context_block = ""
    used_rag = False
    
    if use_rag:
        rag_query = f"{context or ''} {message}".strip()
        rag_chunks = rag_service.retrieve(rag_query, top_k=4)
        rag_context_block = rag_service.format_for_prompt(rag_chunks)
        used_rag = bool(rag_chunks)

    # --- 3. Build the full prompt ---
    persona_instruction = build_persona_instruction(persona)
    parts = [
        f"PERSONA INSTRUCTION: {persona_instruction}",
    ]
    if context:
        parts.append(f"PAGE CONTEXT: The user is currently on the page: {context}")
        
    if intent == "current_election_info":
        parts.append(
            "CRITICAL INSTRUCTION: The user is asking about current, live, or dynamic election information. "
            "You MUST rely exclusively on official or highly reliable sources to answer this. "
            "Specifically, refer to: eci.gov.in, voters.eci.gov.in, official state CEO websites, "
            "or State Election Commission websites. "
            "Do NOT guess or use outdated knowledge. If the search results do not contain a clear, "
            "official answer, state clearly that you cannot verify the latest information and redirect "
            "the user to eci.gov.in."
        )
    elif intent == "current_party_info":
        parts.append(
            "CRITICAL INSTRUCTION: The user is asking about current party leadership or dynamic party information. "
            "You MUST rely exclusively on the party's official website or highly reliable official public sources to answer this. "
            "Do NOT guess or use outdated knowledge. Do NOT show bias. If the search results do not contain a clear, "
            "official answer from a reliable source, state clearly that you cannot verify the latest information and advise "
            "the user to check official party sources."
        )
        
    if rag_context_block:
        parts.append(rag_context_block)
    parts.append(f"USER QUESTION: {message}")
    full_user_prompt = "\n\n".join(parts)

    # --- 4. Build source list ---
    sources = []
    seen_urls = set()
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

    # --- 5. Call Gemini ---
    logger.info(f"Calling Gemini | model={settings.GEMINI_MODEL} | persona={persona} | rag_chunks={len(rag_chunks)} | use_current_info={use_current_info}")

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.4,  # Lower temp = more factual, less creative
            max_output_tokens=800,
        )

        # Optional: Google Search grounding for current info
        used_search = False
        if intent in ("current_election_info", "current_party_info") and settings.ENABLE_GOOGLE_SEARCH_GROUNDING:
            config.tools = [types.Tool(google_search=types.GoogleSearch())]
            used_search = True
            logger.info(f"Google Search grounding ENABLED for intent: {intent}")

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=full_user_prompt,
            config=config,
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

        return ChatResponse(
            answer=answer_text,
            sources=sources,
            safety=SafetyInfo(blocked=False, reason=None),
            meta=MetaInfo(
                model=settings.GEMINI_MODEL, 
                used_rag=used_rag, 
                used_search_grounding=used_search,
                checkedAt=checked_at,
                sourceType=source_type
            )
        )

    except Exception as e:
        error_str = str(e)
        status_code = getattr(e, 'status_code', None) or getattr(e, 'code', None)
        logger.error(f"Gemini error | status={status_code} | type={type(e).__name__} | msg={error_str[:150]}")

        if "API_KEY" in error_str.upper() or status_code in (401, 403):
            raise PermissionError(ERROR_MESSAGES["auth"])
        if status_code == 429 or "quota" in error_str.lower() or "rate" in error_str.lower():
            raise ConnectionError(ERROR_MESSAGES["quota"])
        if status_code == 503 or "overload" in error_str.lower() or "unavailable" in error_str.lower():
            raise ConnectionError(ERROR_MESSAGES["overload"])
        if "timeout" in error_str.lower():
            raise TimeoutError(ERROR_MESSAGES["timeout"])

        raise RuntimeError(ERROR_MESSAGES["unknown"])
