#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Circuit breaker for LLM provider calls (inspired by MEO-AI aiBrain)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from metagpt.logs import logger


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised when a provider circuit is open and calls are blocked.

    Shared code with MEO circuitBreaker.js CircuitOpenError.
    """

    def __init__(self, name: str, failures: int):
        self.name = name
        self.provider = name  # MEO alias
        self.failures = failures
        self.code = "CIRCUIT_OPEN"  # shared with MEO
        super().__init__(f"Circuit breaker OPEN for {name} (failures: {failures})")


@dataclass
class CircuitBreaker:
    """Classic circuit breaker: closed → open → half_open → closed."""

    name: str
    threshold: int = 5
    reset_timeout: float = 60.0
    half_open_max: int = 2
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    last_failure_at: float = 0.0
    half_open_attempts: int = 0
    _lock_note: str = field(default="", repr=False)

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_at >= self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_attempts = 0
                logger.info(f"[circuitBreaker] {self.name} → HALF_OPEN, probing")
                return True
            return False
        # HALF_OPEN
        if self.half_open_attempts < self.half_open_max:
            self.half_open_attempts += 1
            return True
        return False

    def record_success(self) -> None:
        if self.state != CircuitState.CLOSED:
            logger.info(f"[circuitBreaker] {self.name} → CLOSED after success")
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.half_open_attempts = 0

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure_at = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_attempts = 0
            logger.warning(f"[circuitBreaker] {self.name} re-opened from HALF_OPEN")
            return
        if self.failures >= self.threshold and self.state == CircuitState.CLOSED:
            self.state = CircuitState.OPEN
            logger.warning(f"[circuitBreaker] {self.name} OPENED after {self.failures} failures")

    def reset(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.half_open_attempts = 0
        self.last_failure_at = 0.0

    def snapshot(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
            "last_failure_at": self.last_failure_at,
            "half_open_attempts": self.half_open_attempts,
        }


_BREAKERS: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    threshold: int = 5,
    reset_timeout: float = 60.0,
    half_open_max: int = 2,
) -> CircuitBreaker:
    breaker = _BREAKERS.get(name)
    if breaker is None:
        breaker = CircuitBreaker(
            name=name,
            threshold=threshold,
            reset_timeout=reset_timeout,
            half_open_max=half_open_max,
        )
        _BREAKERS[name] = breaker
    return breaker


def reset_circuit_breaker(name: Optional[str] = None) -> None:
    if name is None:
        _BREAKERS.clear()
        return
    breaker = _BREAKERS.get(name)
    if breaker:
        breaker.reset()


def circuit_breaker_status() -> dict:
    return {name: b.snapshot() for name, b in _BREAKERS.items()}


# ── MEO-compatible aliases (circuitBreaker.js) ──────────────────────────

def should_allow_request(name: str) -> bool:
    return get_circuit_breaker(name).allow_request()


def assert_allowed(name: str) -> None:
    breaker = get_circuit_breaker(name)
    if not breaker.allow_request():
        raise CircuitOpenError(name, breaker.failures)


# camelCase aliases
getCircuitBreakerStatus = circuit_breaker_status
resetCircuitBreaker = reset_circuit_breaker
CircuitState_CLOSED = CircuitState.CLOSED
