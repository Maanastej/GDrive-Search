"""
FastAPI Application Entry Point.

Sets up the application, CORS middleware, routes, and health-check
endpoint. This is the module that uvicorn targets.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.schemas import HealthResponse
from app.routes.chat import router as chat_router
from app.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup / shutdown hooks."""
    setup_logging()
    settings = get_settings()
    logger.info(
        "%s v%s starting (debug=%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.DEBUG,
    )
    yield
    logger.info("%s shutting down", settings.APP_NAME)


# ── Application factory ─────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Conversational AI assistant for searching Google Drive files "
            "using natural language."
        ),
        lifespan=lifespan,
    )

    # CORS — allow Streamlit frontend
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(chat_router)

    # Health check
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check() -> HealthResponse:
        return HealthResponse(version=settings.APP_VERSION)

    return app


# ── Module-level app instance (used by `uvicorn app.main:app`) ───────────
app = create_app()
