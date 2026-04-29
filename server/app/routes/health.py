from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/api/health")
async def health():
    return {
        "ok": True,
        "service": "votewise-python-backend",
        "version": "1.0.0",
        "model": settings.GEMINI_MODEL,
        "gemini_key_present": bool(settings.GEMINI_API_KEY),
        "rag_enabled": True,
        "search_grounding_enabled": settings.ENABLE_GOOGLE_SEARCH_GROUNDING,
    }
