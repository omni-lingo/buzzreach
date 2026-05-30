"""In-memory token bucket rate limiter (RATE-001).

Provides per-key rate limiting using the token bucket algorithm.
Keys can represent IPs, user IDs, or provider names. Configuration
is read from Settings (rate_limit_tokens_per_minute, rate_limit_burst_size).

Thread-safe: each bucket uses a threading.Lock to prevent concurrent
corruption.
"""

import logging
import threading
import time
from dataclasses import dataclass, field

from src.backend.settings import Settings

log = logging.getLogger("buzzreach")


@dataclass
class _TokenBucket:
    """Internal state for a single rate-limit key."""

    tokens: float
    burst_size: int
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.monotonic)
    lock: threading.Lock = field(default_factory=threading.Lock)


class RateLimiter:
    """In-memory token bucket rate limiter.

    Each key gets an independent bucket that starts full (at burst_size)
    and refills at the configured rate. check() atomically consumes
    tokens and returns True/False — it never raises.

    Args:
        settings: Application settings providing rate limit config.
    """

    def __init__(self, settings: Settings) -> None:
        self._burst_size = settings.rate_limit_burst_size
        self._refill_rate = settings.rate_limit_tokens_per_minute / 60.0
        self._buckets: dict[str, _TokenBucket] = {}
        self._global_lock = threading.Lock()
        log.info(
            "Rate limiter initialized",
            extra={
                "burst_size": self._burst_size,
                "tokens_per_minute": settings.rate_limit_tokens_per_minute,
            },
        )

    def check(self, key: str, tokens_needed: int = 1) -> bool:
        """Check whether a request identified by *key* is allowed.

        Consumes *tokens_needed* from the bucket if available.

        Args:
            key: Identifier for the rate limit bucket (IP, user_id,
                 provider name).
            tokens_needed: Number of tokens to consume (default 1).

        Returns:
            True if the request is allowed, False if rate-limited.
        """
        bucket = self._get_or_create_bucket(key)
        with bucket.lock:
            self._refill(bucket)
            if bucket.tokens >= tokens_needed:
                bucket.tokens -= tokens_needed
                return True
            log.info(
                "Rate limit exceeded",
                extra={"key": key, "tokens_available": bucket.tokens},
            )
            return False

    def reset(self, key: str) -> None:
        """Reset a key's bucket to full capacity.

        No-op if the key has never been seen.

        Args:
            key: The rate limit key to reset.
        """
        bucket = self._buckets.get(key)
        if bucket is None:
            return
        with bucket.lock:
            bucket.tokens = float(self._burst_size)
            bucket.last_refill = time.monotonic()

    def _get_or_create_bucket(self, key: str) -> _TokenBucket:
        """Return the bucket for *key*, creating it if needed."""
        bucket = self._buckets.get(key)
        if bucket is not None:
            return bucket
        with self._global_lock:
            # Double-check after acquiring lock
            bucket = self._buckets.get(key)
            if bucket is not None:
                return bucket
            bucket = _TokenBucket(
                tokens=float(self._burst_size),
                burst_size=self._burst_size,
                refill_rate=self._refill_rate,
            )
            self._buckets[key] = bucket
            return bucket

    @staticmethod
    def _refill(bucket: _TokenBucket) -> None:
        """Add tokens to *bucket* based on elapsed time.

        Tokens are capped at ``burst_size``. Caller must hold
        ``bucket.lock``.
        """
        now = time.monotonic()
        elapsed = now - bucket.last_refill
        if elapsed <= 0:
            return
        new_tokens = elapsed * bucket.refill_rate
        bucket.tokens = min(
            bucket.tokens + new_tokens,
            float(bucket.burst_size),
        )
        bucket.last_refill = now
