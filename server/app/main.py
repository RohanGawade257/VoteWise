import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routes import health, chat
from app.services import rag_service
from app.utils.logging import get_logger

logger = get_logger("main")


# ---------------------------------------------------------------------------
# Rate limiter — key by real IP, respects CHAT_RATE_LIMIT env var
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("VoteWise backend starting up...")
    logger.info(f"Rate limiting enabled: {settings.RATE_LIMIT_ENABLED}")
    logger.info(f"Chat rate limit: {settings.CHAT_RATE_LIMIT}")
    rag_service.load_knowledge()
    logger.info(f"Gemini model: {settings.GEMINI_MODEL}")
    logger.info(f"Search grounding: {settings.ENABLE_GOOGLE_SEARCH_GROUNDING}")
    yield
    logger.info("VoteWise backend shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="VoteWise API",
    description="Neutral civic education AI assistant for Indian voters.",
    version="1.0.0",
    lifespan=lifespan,
    # Hide default /docs in production
    docs_url="/docs" if os.getenv("NODE_ENV", "development") == "development" else None,
    redoc_url=None,
)

# Attach rate limiter state BEFORE routes are included
app.state.limiter = limiter


# ---------------------------------------------------------------------------
# Exception handlers — registered BEFORE middleware
# ---------------------------------------------------------------------------

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(
        f"Rate limit exceeded | ip={request.client.host} | path={request.url.path}"
    )
    return JSONResponse(
        status_code=429,
        content={
            "answer": "Too many requests. Please wait a moment and try again.",
            "sources": [],
            "safety": {"blocked": True, "reason": "rate_limit"},
            "meta": {"rate_limited": True, "used_model": False, "used_rag": False},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Extract a user-friendly message without leaking internal details
    errors = exc.errors()
    first = errors[0] if errors else {}
    loc = " → ".join(str(l) for l in first.get("loc", []))
    msg = first.get("msg", "invalid input")
    logger.warning(
        f"Request validation error | path={request.url.path} | loc={loc} | msg={msg}"
    )
    return JSONResponse(
        status_code=422,
        content={
            "answer": "Please enter a valid question under 1500 characters.",
            "sources": [],
            "safety": {"blocked": True, "reason": "invalid_input"},
            "meta": {"used_model": False, "used_rag": False},
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    # For API routes: always JSON
    if request.url.path.startswith("/api/"):
        logger.warning(
            f"HTTP {exc.status_code} on API route | path={request.url.path}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc.detail)},
        )
    # For non-API 404s (unknown frontend routes): serve React SPA
    if exc.status_code == 404:
        index_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "client", "dist", "index.html"
        )
        if os.path.isfile(index_path):
            return FileResponse(index_path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log full exception type for backend debugging, never expose to client
    logger.error(
        f"Unhandled exception | type={type(exc).__name__} | path={request.url.path}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "answer": (
                "Something went wrong while preparing the answer. "
                "Please try again, or check official ECI sources."
            ),
            "sources": [],
            "safety": {"blocked": True, "reason": "internal_error"},
            "meta": {"used_model": False, "used_rag": False},
        },
    )


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGIN, "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(chat.router)

# ---------------------------------------------------------------------------
# Serve React frontend static files in production
# ---------------------------------------------------------------------------
CLIENT_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "client", "dist")
if os.path.isdir(CLIENT_DIST):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(CLIENT_DIST, "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        return FileResponse(os.path.join(CLIENT_DIST, "index.html"))

    logger.info(f"Serving React frontend from {CLIENT_DIST}")
