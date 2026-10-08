#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for shared RetryPolicy + RateLimiter (MEO twin)."""

import asyncio
import time
import unittest

from metagpt.provider.rate_limiter import RateLimiter, RateLimitConfig
from metagpt.provider.retry_policy import RetryPolicy, with_retry


class FakeRateLimitErr(Exception):
    def __init__(self):
        super().__init__("429 Too Many Requests")
        self.status = 429
        self.headers = {"retry-after": "0"}


class FakeTimeoutErr(Exception):
    def __init__(self):
        super().__init__("fetch failed: timeout")
        self.name = "TimeoutError"


class PermanentErr(Exception):
    def __init__(self):
        super().__init__("invalid api key")
        self.status = 401


class TestRetryPolicy(unittest.TestCase):
    def test_exponential_backoff(self):
        p = RetryPolicy(base_delay_ms=100, max_delay_ms=10000, backoff_multiplier=2, jitter_ms=0)
        self.assertAlmostEqual(p.calculate_delay(0), 100)
        self.assertAlmostEqual(p.calculate_delay(1), 200)
        self.assertAlmostEqual(p.calculate_delay(2), 400)

    def test_max_delay_cap(self):
        p = RetryPolicy(base_delay_ms=1000, max_delay_ms=1500, backoff_multiplier=10, jitter_ms=0)
        self.assertAlmostEqual(p.calculate_delay(3), 1500)

    def test_respect_retry_after(self):
        p = RetryPolicy()
        self.assertAlmostEqual(p.calculate_delay(0, retry_after_ms=2500), 2500)

    def test_is_rate_limit(self):
        self.assertTrue(RetryPolicy.is_rate_limit(FakeRateLimitErr()))
        self.assertFalse(RetryPolicy.is_rate_limit(PermanentErr()))

    def test_is_retryable(self):
        self.assertTrue(RetryPolicy.is_retryable(FakeTimeoutErr()))
        self.assertTrue(RetryPolicy.is_retryable(FakeRateLimitErr()))
        self.assertFalse(RetryPolicy.is_retryable(PermanentErr()))

    def test_with_retry_succeeds_after_failures(self):
        calls = {"n": 0}

        async def fn():
            calls["n"] += 1
            if calls["n"] < 3:
                raise FakeTimeoutErr()
            return "ok"

        p = RetryPolicy(max_retries=3, base_delay_ms=1, jitter_ms=0)
        out = asyncio.run(with_retry(fn, policy=p))
        self.assertEqual(out, "ok")
        self.assertEqual(calls["n"], 3)

    def test_with_retry_gives_up(self):
        async def fn():
            raise PermanentErr()

        p = RetryPolicy(max_retries=2, base_delay_ms=1, jitter_ms=0)
        with self.assertRaises(PermanentErr):
            asyncio.run(with_retry(fn, policy=p))


class TestRateLimiter(unittest.TestCase):
    def test_allows_under_limit(self):
        rl = RateLimiter(RateLimitConfig(max_requests=5, window_sec=60, max_concurrent=10))
        for _ in range(5):
            r = rl.try_acquire("p")
            self.assertTrue(r["allowed"])
        r = rl.try_acquire("p")
        self.assertFalse(r["allowed"])
        self.assertGreater(r["retryAfterMs"], 0)

    def test_release_concurrency(self):
        rl = RateLimiter(RateLimitConfig(max_requests=100, window_sec=60, max_concurrent=1))
        self.assertTrue(rl.try_acquire("k")["allowed"])
        blocked = rl.try_acquire("k")
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked.get("reason"), "max_concurrent")
        rl.release("k")
        self.assertTrue(rl.try_acquire("k")["allowed"])

    def test_keys_are_isolated(self):
        rl = RateLimiter(RateLimitConfig(max_requests=1, window_sec=60, max_concurrent=10))
        self.assertTrue(rl.try_acquire("a")["allowed"])
        self.assertFalse(rl.try_acquire("a")["allowed"])
        self.assertTrue(rl.try_acquire("b")["allowed"])

    def test_acquire_async_waits(self):
        rl = RateLimiter(RateLimitConfig(max_requests=2, window_sec=0.05, max_concurrent=10))
        self.assertTrue(rl.try_acquire("x")["allowed"])
        self.assertTrue(rl.try_acquire("x")["allowed"])
        # window almost expired — acquire should wait and succeed
        time.sleep(0.06)
        r = asyncio.run(rl.acquire("x", max_wait_ms=1000, poll_ms=20))
        self.assertTrue(r["allowed"])

    def test_status_shape(self):
        rl = RateLimiter()
        rl.try_acquire("z")
        s = rl.status()
        self.assertIn("config", s)
        self.assertIn("z", s["keys"])


if __name__ == "__main__":
    unittest.main()
