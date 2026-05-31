"""FastAPI application factory (API-001).

Creates the FastAPI app with CORS restricted to explicit origins,
mounts v1 routers, and configures middleware. CORS never uses ``["*"]``
(BUILD_RULES gate 7).
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.auth import router as auth_router
from src.backend.api.billing import router as billing_router
from src.backend.api.push import router as push_router
from src.backend.api.slack_webhooks import router as slack_router
from src.backend.api.v1.dashboard import router as dashboard_router
from src.backend.api.v1.opportunities import router as opportunities_router
from src.backend.api.webhooks import router as webhooks_router
from src.backend.settings import Settings

log = logging.getLogger("buzzreach.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Optional settings override (uses defaults if None).

    Returns:
        Configured FastAPI instance with routers and middleware.
    """
    settings = settings or Settings()

    app = FastAPI(
        title="BuzzReach API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(auth_router)
    app.include_router(billing_router)
    app.include_router(dashboard_router)
    app.include_router(opportunities_router)
    app.include_router(push_router)
    app.include_router(slack_router)
    app.include_router(webhooks_router)

    log.info(
        "App created",
        extra={"cors_origins": settings.cors_allowed_origins},
    )

    return app
