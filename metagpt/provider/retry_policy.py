#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Retry policy — shared with MEO server/ai/retryPolicy.js.

Shared contract:
  maxRetries, baseDelayMs, maxDelayMs, backoffMultiplier
  calculate_delay(attempt) -> ms
  is_rate_limit(error) -> bool
  is_retryable(error) -> bool
  get_retry_after_ms(error) -> Optional[int]
  async with_retry(fn, policy=..., on_retry=...) 
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, TypeVar

from metagpt.logs import logger

T = TypeVar("T")

# HTTP status codes treated as rate limit / transient
RATE_LIMIT_STATUS = {429}
TRANSIENT_STATUS = {408, 425, 500, 502, 503, 504}
TRANSIENT_NAMES = {
    "AbortError",
    "TimeoutError",
    "APIConnectionError",
    "APITimeoutError",
    "RateLimitError",
    "ServiceUnavailableError",
}
TRANSIENT_SUBSTRINGS = (
    "timeout",
    "timed out",
    "econnreset",
    "econnrefused",
    "fetch failed",
    "connection",
    "temporarily unavailable",
    "rate limit",
    "too many requests",
)


@dataclass
class RetryPolicy:
    """Exponential backoff + jitter — MEO RETRY_CONFIG twin."""

    max_retries: int = 2
    base_delay_ms: float = 1000.0
    max_delay_ms: float = 10000.0
    backoff_multiplier: float = 2.0
    jitter_ms: float = 500.0
    respect_retry_after: bool = True

    # ── camelCase shared API ──────────────────────────────────────────

    @property
    def maxRetries(self) -> int:
        return self.max_retries

    @property
    def baseDelayMs(self) -> float:
        return self.base_delay_ms

    def calculate_delay(self, attempt: int, retry_after_ms: Optional[float] = None) -> float:
        """Delay before next attempt (attempt is 0-based)."""
        if self.respect_retry_after and retry_after_ms is not None and retry_after_ms >= 0:
            return float(retry_after_ms)
        delay = self.base_delay_ms * (self.backoff_multiplier**attempt)
        delay = min(delay, self.max_delay_ms)
        if self.jitter_ms:
            delay += random.uniform(0, self.jitter_ms)
        return delay

    calculateDelay = calculate_delay

    @staticmethod
    def get_retry_after_ms(error: Any) -> Optional[float]:
        """Parse Retry-After from exception (seconds or HTTP-date ignored → numeric only)."""
        headers = getattr(error, "headers", None) or getattr(error, "response", None)
        if headers is not None and hasattr(headers, "get"):
            raw = headers.get("retry-after") or headers.get("Retry-After")
            if raw is not None:
                try:
                    return float(raw) * 1000.0
                except (TypeError, ValueError):
                    pass
        # OpenAI SDK style: error.response.headers
        resp = getattr(error, "response", None)
        if resp is not None:
            h = getattr(resp, "headers", None)
            if h is not None and hasattr(h, "get"):
                raw = h.get("retry-after") or h.get("Retry-After")
                if raw is not None:
                    try:
                        return float(raw) * 1000.0
                    except (TypeError, ValueError):
                        pass
        return None

    getRetryAfterMs = get_retry_after_ms

    @staticmethod
    def is_rate_limit(error: Any) -> bool:
        status = getattr(error, "status", None) or getattr(error, "code", None)
        if isinstance(status, int) and status in RATE_LIMIT_STATUS:
            return True
        status_code = getattr(getattr(error, "response", None), "status_code", None)
        if isinstance(status_code, int) and status_code in RATE_LIMIT_STATUS:
            return True
        name = type(error).__name__
        if name in ("RateLimitError",):
            return True
        msg = str(error).lower()
        return "rate limit" in msg or "too many requests" in msg or "429" in msg

    isRateLimit = is_rate_limit

    @staticmethod
    def is_retryable(error: Any) -> bool:
        if RetryPolicy.is_rate_limit(error):
            return True
        status = getattr(error, "status", None)
        if isinstance(status, int) and status in TRANSIENT_STATUS:
            return True
        status_code = getattr(getattr(error, "response", None), "status_code", None)
        if isinstance(status_code, int) and status_code in TRANSIENT_STATUS:
            return True
        name = type(error).__name__
        if name in TRANSIENT_NAMES:
            return True
        if isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return True
        msg = str(error).lower()
        return any(s in msg for s in TRANSIENT_SUBSTRINGS)

    isRetryable = is_retryable

    def snapshot(self) -> dict:
        return {
            "maxRetries": self.max_retries,
            "baseDelayMs": self.base_delay_ms,
            "maxDelayMs": self.max_delay_ms,
            "backoffMultiplier": self.backoff_multiplier,
            "jitterMs": self.jitter_ms,
        }


DEFAULT_RETRY_POLICY = RetryPolicy()


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    policy: Optional[RetryPolicy] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
) -> T:
    """Run async fn with retry. fn must be a zero-arg factory returning a coroutine."""
    policy = policy or DEFAULT_RETRY_POLICY
    last_exc: Optional[Exception] = None
    for attempt in range(policy.max_retries + 1):
        try:
            return await fn()
        except Exception as e:
            last_exc = e
            if not policy.is_retryable(e) or attempt >= policy.max_retries:
                raise
            retry_after = policy.get_retry_after_ms(e) if policy.respect_retry_after else None
            wait_ms = policy.calculate_delay(attempt, retry_after_ms=retry_after)
            logger.warning(
                f"[retry] attempt {attempt + 1}/{policy.max_retries + 1} failed "
                f"({type(e).__name__}: {e}); waiting {wait_ms:.0f}ms"
            )
            if on_retry:
                on_retry(attempt, e, wait_ms)
            await asyncio.sleep(wait_ms / 1000.0)
    raise last_exc  # pragma: no cover
