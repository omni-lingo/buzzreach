"""Rate limiting dependency for API endpoints (API-001).

Uses the RATE-001 RateLimiter service to enforce per-IP request quotas.
Injected via ``Depends(require_rate_limit)`` on protected routes.
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from src.backend.services.auth.rate_limiter import RateLimiter
from src.backend.settings import Settings

log = logging.getLogger("buzzreach.api.rate_limit")

_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Return the singleton RateLimiter instance."""
    global _rate_limiter  # noqa: PLW0603
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(Settings())
    return _rate_limiter


def require_rate_limit(
    request: Request,
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Check rate limit for the requesting IP.

    Raises:
        HTTPException: 429 if the IP has exceeded its quota.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.check(client_ip):
        log.info(
            "Rate limit exceeded",
            extra={"ip": client_ip},
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
            },
        )
