"""
Gemini Service — Handles all Google Gemini API calls.
Uses google-genai SDK. Never logs or exposes the API key.
"""
from google import genai
from google.genai import types
from app.config import settings
from app.prompts.system_prompt import SYSTEM_PROMPT, build_persona_instruction
from app.services import rag_service
from app.utils.logging import get_logger
from app.models import ChatResponse, SourceItem, SafetyInfo, MetaInfo

logger = get_logger("gemini_service")

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
    use_current_info: bool
) -> ChatResponse:

    # --- 1. Check API key ---
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is missing from environment.")
        raise ValueError(ERROR_MESSAGES["no_key"])

    # --- 2. RAG retrieval ---
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
        if use_current_info and settings.ENABLE_GOOGLE_SEARCH_GROUNDING:
            config.tools = [types.Tool(google_search=types.GoogleSearch())]
            used_search = True
            logger.info("Google Search grounding ENABLED for this request")

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=full_user_prompt,
            config=config,
        )

        answer_text = response.text
        if not answer_text:
            raise ValueError("Empty response from Gemini.")

        # Extract grounding citations if search was used
        if used_search and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                    for gc in gm.grounding_chunks[:3]:
                        if hasattr(gc, 'web') and gc.web:
                            sources.append(SourceItem(title=gc.web.title or "Web Source", url=gc.web.uri, type="web"))

        logger.info(f"Gemini response OK | length={len(answer_text)} chars | search_grounded={used_search}")

        return ChatResponse(
            answer=answer_text,
            sources=sources,
            safety=SafetyInfo(blocked=False, reason=None),
            meta=MetaInfo(model=settings.GEMINI_MODEL, used_rag=used_rag, used_search_grounding=used_search)
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
