"""Tests for RATE-001: Token bucket rate limiter (in-memory).

Covers: requests allowed until quota exhausted, requests denied after
exhaustion, bucket refills over time (mocked), reset clears bucket,
multiple independent keys, thread safety under concurrent access.
"""

from unittest.mock import patch

import pytest

from src.backend.services.auth.rate_limiter import RateLimiter
from src.backend.settings import Settings


@pytest.fixture()
def settings() -> Settings:
    """Settings with a small bucket for easy testing."""
    return Settings(
        rate_limit_tokens_per_minute=60,
        rate_limit_burst_size=10,
    )


@pytest.fixture()
def limiter(settings: Settings) -> RateLimiter:
    """RateLimiter wired with test settings."""
    return RateLimiter(settings=settings)


class TestCheckAllowsUntilExhausted:
    """check() returns True until the bucket runs dry."""

    def test_first_request_allowed(self, limiter: RateLimiter) -> None:
        assert limiter.check("192.168.1.1") is True

    def test_allows_up_to_burst_size(self, limiter: RateLimiter) -> None:
        key = "user-1"
        results = [limiter.check(key) for _ in range(10)]
        assert all(results)

    def test_denies_after_burst_exhausted(
        self, limiter: RateLimiter,
    ) -> None:
        key = "user-2"
        for _ in range(10):
            limiter.check(key)
        assert limiter.check(key) is False

    def test_multi_token_request(self, limiter: RateLimiter) -> None:
        key = "bulk-op"
        assert limiter.check(key, tokens_needed=5) is True
        assert limiter.check(key, tokens_needed=5) is True
        assert limiter.check(key, tokens_needed=1) is False

    def test_check_never_raises(self, limiter: RateLimiter) -> None:
        key = "safe-key"
        for _ in range(20):
            result = limiter.check(key)
            assert isinstance(result, bool)


class TestBucketRefill:
    """Bucket refills tokens over time."""

    def test_refills_after_time_passes(self, limiter: RateLimiter) -> None:
        key = "refill-test"
        # Drain the bucket
        for _ in range(10):
            limiter.check(key)
        assert limiter.check(key) is False

        # Advance time by 10 seconds → 60 tokens/min = 1 token/sec → +10
        with patch("src.backend.services.auth.rate_limiter.time") as mock_time:
            # First call to time() was during init/check; now advance
            mock_time.monotonic.return_value = (
                limiter._buckets[key].last_refill + 10.0
            )
            assert limiter.check(key) is True

    def test_refill_does_not_exceed_burst(
        self, limiter: RateLimiter,
    ) -> None:
        key = "cap-test"
        # Use 5 tokens
        for _ in range(5):
            limiter.check(key)

        # Advance 600 seconds (way more than needed to fill bucket)
        with patch("src.backend.services.auth.rate_limiter.time") as mock_time:
            mock_time.monotonic.return_value = (
                limiter._buckets[key].last_refill + 600.0
            )
            # Should allow burst_size requests, not more
            results = [limiter.check(key) for _ in range(10)]
            assert all(results)
            assert limiter.check(key) is False


class TestIndependentKeys:
    """Each key has its own independent bucket."""

    def test_different_keys_independent(
        self, limiter: RateLimiter,
    ) -> None:
        # Exhaust key A
        for _ in range(10):
            limiter.check("key-a")
        assert limiter.check("key-a") is False

        # Key B unaffected
        assert limiter.check("key-b") is True

    def test_ip_and_provider_keys_independent(
        self, limiter: RateLimiter,
    ) -> None:
        for _ in range(10):
            limiter.check("10.0.0.1")
        assert limiter.check("10.0.0.1") is False
        assert limiter.check("search_provider") is True


class TestReset:
    """reset() restores a key's bucket to full capacity."""

    def test_reset_restores_tokens(self, limiter: RateLimiter) -> None:
        key = "reset-me"
        for _ in range(10):
            limiter.check(key)
        assert limiter.check(key) is False

        limiter.reset(key)
        assert limiter.check(key) is True

    def test_reset_unknown_key_is_noop(
        self, limiter: RateLimiter,
    ) -> None:
        limiter.reset("never-seen")  # Should not raise


class TestThreadSafety:
    """Concurrent access does not corrupt bucket state."""

    def test_concurrent_checks_do_not_over_allow(self) -> None:
        import threading

        settings = Settings(
            rate_limit_tokens_per_minute=60,
            rate_limit_burst_size=50,
        )
        limiter = RateLimiter(settings=settings)
        key = "concurrent"
        allowed_count = 0
        lock = threading.Lock()

        def drain() -> None:
            nonlocal allowed_count
            local_allowed = 0
            for _ in range(20):
                if limiter.check(key):
                    local_allowed += 1
            with lock:
                allowed_count += local_allowed

        threads = [threading.Thread(target=drain) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 5 threads × 20 attempts = 100, but only 50 tokens available
        assert allowed_count == 50
