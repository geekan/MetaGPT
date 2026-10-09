#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Streaming helpers — shared with MEO server/ai/streaming.js.

Shared contract:
  StreamAccumulator: push(delta), end(), text, chunks
  estimate_tokens(text)
  create_stream_collector(on_token=None) -> collector with push/end/finalize
"""

from __future__ import annotations

import math
from typing import Any, Callable, List, Optional

from metagpt.logs import logger
from metagpt.provider.token_usage import normalize_usage


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token English heuristic)."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


class StreamAccumulator:
    """Collect stream deltas into final text + optional usage (MEO twin)."""

    def __init__(
        self,
        on_token: Optional[Callable[[str], None]] = None,
        model: str = "",
        provider: str = "",
    ):
        self.on_token = on_token
        self.model = model
        self.provider = provider
        self._chunks: List[str] = []
        self._finished = False
        self._usage: Optional[dict] = None

    def push(self, delta: str) -> None:
        """Append one stream chunk. Empty deltas ignored."""
        if not delta or self._finished:
            return
        self._chunks.append(delta)
        if self.on_token:
            try:
                self.on_token(delta)
            except Exception as e:  # user callback must not break stream
                logger.warning(f"[stream] on_token callback failed: {e}")

    def set_usage(self, usage: Any) -> None:
        """Attach provider usage (dict or object) from final chunk."""
        self._usage = normalize_usage(usage)

    @property
    def text(self) -> str:
        return "".join(self._chunks)

    @property
    def chunks(self) -> list[str]:
        return list(self._chunks)

    @property
    def finished(self) -> bool:
        return self._finished

    def end(self) -> dict:
        """Finalize; returns { text, usage, chunks }."""
        self._finished = True
        text = self.text
        usage = self._usage
        if usage is None or not usage.get("totalTokens"):
            # estimate completion tokens when provider omitted usage
            pt = usage.get("promptTokens", 0) if usage else 0
            ct = estimate_tokens(text)
            usage = normalize_usage(usage, prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct)
        return {
            "text": text,
            "usage": usage,
            "chunks": len(self._chunks),
            "model": self.model,
            "provider": self.provider,
        }


class StreamCollector(StreamAccumulator):
    """Alias kept for shared naming with JS createStreamCollector."""

    def finalize(self) -> dict:
        return self.end()


def create_stream_collector(
    on_token: Optional[Callable[[str], None]] = None,
    model: str = "",
    provider: str = "",
) -> StreamCollector:
    return StreamCollector(on_token=on_token, model=model, provider=provider)


def collect_stream_text(chunks, on_token: Optional[Callable[[str], None]] = None) -> str:
    """Helper: consume an async chunk iterator into a string."""
    # sync-friendly for tests; async path uses StreamAccumulator in providers
    acc = create_stream_collector(on_token=on_token)
    for c in chunks:
        acc.push(c if isinstance(c, str) else str(c))
    acc.end()
    return acc.text
