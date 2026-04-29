import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routes import health, chat
from app.services import rag_service
from app.utils.logging import get_logger

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load RAG knowledge base
    logger.info("VoteWise backend starting up...")
    rag_service.load_knowledge()
    logger.info(f"Gemini model: {settings.GEMINI_MODEL}")
    logger.info(f"Search grounding: {settings.ENABLE_GOOGLE_SEARCH_GROUNDING}")
    yield
    logger.info("VoteWise backend shutting down.")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="VoteWise API",
    description="Neutral civic education AI assistant for Indian voters.",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGIN, "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# API routes
app.include_router(health.router)
app.include_router(chat.router)

# Serve React frontend static files in production
CLIENT_DIST = os.path.join(os.path.dirname(__file__), '..', '..', 'client', 'dist')
if os.path.isdir(CLIENT_DIST):
    from fastapi.responses import FileResponse
    app.mount("/assets", StaticFiles(directory=os.path.join(CLIENT_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        index = os.path.join(CLIENT_DIST, "index.html")
        return FileResponse(index)

    logger.info(f"Serving React frontend from {CLIENT_DIST}")
