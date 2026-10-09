#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rate limiter — sliding-window per key. Shared with MEO server/ai/rateLimiter.js.

Shared contract:
  try_acquire(key) -> { allowed, remaining, retryAfterMs, limit }
  acquire(key) -> await until allowed (optional max_wait_ms)
  reset(key=None)
  status() -> dict
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional

from metagpt.logs import logger


@dataclass
class RateLimitConfig:
    """Sliding window limits (per key / provider)."""

    max_requests: int = 60
    window_sec: float = 60.0
    # Optional concurrency cap (in-flight)
    max_concurrent: int = 8


@dataclass
class _Bucket:
    hits: Deque[float] = field(default_factory=deque)
    in_flight: int = 0


class RateLimiter:
    """Sliding-window + optional concurrency limiter (MEO twin)."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._buckets: Dict[str, _Bucket] = {}

    def _bucket(self, key: str) -> _Bucket:
        if key not in self._buckets:
            self._buckets[key] = _Bucket()
        return self._buckets[key]

    def _prune(self, b: _Bucket, now: float) -> None:
        window = self.config.window_sec
        while b.hits and now - b.hits[0] >= window:
            b.hits.popleft()

    def try_acquire(self, key: str = "default") -> dict:
        """Non-blocking acquire. Returns shared status dict."""
        now = time.time()
        b = self._bucket(key)
        self._prune(b, now)

        limit = self.config.max_requests
        window = self.config.window_sec
        max_conc = self.config.max_concurrent

        if len(b.hits) >= limit:
            oldest = b.hits[0]
            retry_after_ms = max(0.0, (oldest + window - now) * 1000.0)
            return {
                "allowed": False,
                "remaining": 0,
                "limit": limit,
                "retryAfterMs": retry_after_ms,
                "key": key,
            }

        if b.in_flight >= max_conc:
            return {
                "allowed": False,
                "remaining": max(0, limit - len(b.hits)),
                "limit": limit,
                "retryAfterMs": 250.0,
                "key": key,
                "reason": "max_concurrent",
            }

        b.hits.append(now)
        b.in_flight += 1
        return {
            "allowed": True,
            "remaining": max(0, limit - len(b.hits)),
            "limit": limit,
            "retryAfterMs": 0.0,
            "key": key,
        }

    tryAcquire = try_acquire

    def release(self, key: str = "default") -> None:
        b = self._bucket(key)
        if b.in_flight > 0:
            b.in_flight -= 1

    async def acquire(
        self,
        key: str = "default",
        max_wait_ms: float = 30000.0,
        poll_ms: float = 100.0,
    ) -> dict:
        """Wait until allowed or max_wait_ms elapsed."""
        deadline = time.time() + max_wait_ms / 1000.0
        while True:
            result = self.try_acquire(key)
            if result["allowed"]:
                return result
            if time.time() >= deadline:
                logger.warning(f"[rateLimiter] acquire timeout key={key}")
                return result
            wait = min(result.get("retryAfterMs") or poll_ms, max(poll_ms, 50.0))
            await asyncio.sleep(wait / 1000.0)

    acquireAsync = acquire

    def reset(self, key: Optional[str] = None) -> None:
        if key is None:
            self._buckets.clear()
            return
        self._buckets.pop(key, None)

    def status(self) -> dict:
        out = {}
        now = time.time()
        for key, b in self._buckets.items():
            self._prune(b, now)
            out[key] = {
                "count": len(b.hits),
                "limit": self.config.max_requests,
                "inFlight": b.in_flight,
                "maxConcurrent": self.config.max_concurrent,
            }
        return {
            "config": {
                "maxRequests": self.config.max_requests,
                "windowSec": self.config.window_sec,
                "maxConcurrent": self.config.max_concurrent,
            },
            "keys": out,
        }


# Process-wide default limiter (env-overridable)
import os  # noqa: E402


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


DEFAULT_RATE_LIMITER = RateLimiter(
    RateLimitConfig(
        max_requests=_env_int("AI_RATE_LIMIT_MAX", 60),
        window_sec=_env_float("AI_RATE_LIMIT_WINDOW_SEC", 60.0),
        max_concurrent=_env_int("AI_RATE_LIMIT_MAX_CONCURRENT", 8),
    )
)


def get_rate_limiter() -> RateLimiter:
    return DEFAULT_RATE_LIMITER
