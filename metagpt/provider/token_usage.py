#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TokenUsage tracker — shared with MEO server/ai/tokenUsage.js.

Shared contract:
  normalize_usage(raw) -> { promptTokens, completionTokens, totalTokens }
  record({promptTokens, completionTokens, totalTokens, model, provider}) -> last usage
  last() / totals() / snapshot() / reset()
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from metagpt.logs import logger


def normalize_usage(raw: Any = None, **kwargs: Any) -> dict:
    """Normalize heterogeneous usage payloads (OpenAI / Anthropic / Gemini / dict)."""
    # Merge kwargs into raw
    data: Dict[str, Any] = {}
    if isinstance(raw, dict):
        data.update(raw)
    elif raw is not None and hasattr(raw, "model_dump"):
        try:
            data.update(raw.model_dump())
        except Exception:
            pass
    elif raw is not None:
        for attr in ("prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"):
            if hasattr(raw, attr):
                data[attr] = getattr(raw, attr)
    data.update({k: v for k, v in kwargs.items() if v is not None})

    def _int(v) -> int:
        try:
            return int(v or 0)
        except (TypeError, ValueError):
            return 0

    # OpenAI chat
    pt = _int(data.get("prompt_tokens"))
    ct = _int(data.get("completion_tokens"))
    tt = _int(data.get("total_tokens"))
    # Anthropic / Responses API aliases
    if not pt:
        pt = _int(data.get("input_tokens"))
    if not ct:
        ct = _int(data.get("output_tokens"))
    if not tt:
        tt = pt + ct
    if not tt and (pt or ct):
        tt = pt + ct
    return {
        "promptTokens": pt,
        "completionTokens": ct,
        "totalTokens": tt,
    }


class TokenUsageTracker(BaseModel):
    """Accumulate token usage across calls (shared interface)."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    last_usage: dict = Field(default_factory=dict)
    by_model: dict[str, dict] = Field(default_factory=dict)
    by_provider: dict[str, dict] = Field(default_factory=dict)

    def record(
        self,
        promptTokens: int = 0,
        completionTokens: int = 0,
        totalTokens: int = 0,
        model: str = "",
        provider: str = "",
        usage: Any = None,
        **kwargs: Any,
    ) -> dict:
        if usage is not None or (promptTokens or completionTokens or totalTokens):
            norm = normalize_usage(
                usage,
                prompt_tokens=promptTokens,
                completion_tokens=completionTokens,
                total_tokens=totalTokens,
                **kwargs,
            )
        else:
            norm = normalize_usage(**kwargs)

        pt, ct, tt = norm["promptTokens"], norm["completionTokens"], norm["totalTokens"]
        # When only total known, count as completion (CostManager-style)
        if not pt and not ct and tt:
            ct = tt
            norm["completionTokens"] = ct
        self.total_prompt_tokens += pt
        self.total_completion_tokens += ct
        self.total_tokens += tt or (pt + ct)
        self.calls += 1
        entry = {
            "promptTokens": pt,
            "completionTokens": ct,
            "totalTokens": tt or (pt + ct),
            "model": model,
            "provider": provider,
        }
        self.last_usage = entry

        m = model or "unknown"
        mc = self.by_model.setdefault(m, {"promptTokens": 0, "completionTokens": 0, "totalTokens": 0, "calls": 0})
        mc["promptTokens"] += pt
        mc["completionTokens"] += ct
        mc["totalTokens"] += tt or (pt + ct)
        mc["calls"] += 1

        if provider:
            pc = self.by_provider.setdefault(
                provider, {"promptTokens": 0, "completionTokens": 0, "totalTokens": 0, "calls": 0}
            )
            pc["promptTokens"] += pt
            pc["completionTokens"] += ct
            pc["totalTokens"] += tt or (pt + ct)
            pc["calls"] += 1

        logger.debug(f"[tokenUsage] last={entry}")
        return entry

    def last(self) -> dict:
        return dict(self.last_usage)

    def totals(self) -> dict:
        return {
            "promptTokens": self.total_prompt_tokens,
            "completionTokens": self.total_completion_tokens,
            "totalTokens": self.total_tokens,
            "calls": self.calls,
        }

    def snapshot(self) -> dict:
        return {
            **self.totals(),
            "last": self.last(),
            "byModel": {k: dict(v) for k, v in self.by_model.items()},
            "byProvider": {k: dict(v) for k, v in self.by_provider.items()},
        }

    def reset(self) -> dict:
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.calls = 0
        self.last_usage = {}
        self.by_model = {}
        self.by_provider = {}
        return self.totals()

    # camelCase aliases
    def recordUsage(self, **kwargs):
        return self.record(**kwargs)

    def getTotals(self):
        return self.totals()

    def getSnapshot(self):
        return self.snapshot()


DEFAULT_TOKEN_USAGE_TRACKER = TokenUsageTracker()


def get_token_usage_tracker() -> TokenUsageTracker:
    return DEFAULT_TOKEN_USAGE_TRACKER
