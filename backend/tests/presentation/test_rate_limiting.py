"""Tests for rate limiting middleware."""
from __future__ import annotations

from tdp.presentation.http.middleware.rate_limiting import SlidingWindowRateLimiter


class TestSlidingWindowRateLimiter:
    def test_allows_within_limit(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=5)
        for _ in range(5):
            allowed, _, _ = limiter.is_allowed("c1")
            assert allowed

    def test_blocks_over_limit(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=2)
        limiter.is_allowed("c1")
        limiter.is_allowed("c1")
        allowed, remaining, _ = limiter.is_allowed("c1")
        assert not allowed
        assert remaining == 0

    def test_different_clients_independent(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=1)
        a1, _, _ = limiter.is_allowed("c1")
        a2, _, _ = limiter.is_allowed("c2")
        assert a1
        assert a2

    def test_remaining_decrements(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=3)
        _, r1, _ = limiter.is_allowed("c1")
        _, r2, _ = limiter.is_allowed("c1")
        _, r3, _ = limiter.is_allowed("c1")
        assert r1 == 2
        assert r2 == 1
        assert r3 == 0

    def test_max_requests_property(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=100)
        assert limiter.max_requests == 100
