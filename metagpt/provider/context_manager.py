#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ContextManager — shared message-window management (MEO contextManager.js twin).

Shared contract:
  append(role, content, **meta) / add_message(msg)
  messages() -> list[{role, content}]
  trim(max_messages, max_chars) -> messages
  system(text) / clear()
  snapshot() / token_estimate()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from metagpt.logs import logger
from metagpt.provider.streaming import estimate_tokens


def estimate_message_tokens(messages: List[dict]) -> int:
    total = 0
    for m in messages:
        content = m.get("content") or ""
        if isinstance(content, list):
            # multimodal content parts
            content = " ".join(str(p.get("text", p)) if isinstance(p, dict) else str(p) for p in content)
        total += estimate_tokens(str(content)) + 4  # role overhead
    return total


class ContextManager(BaseModel):
    """Bounded chat context: pin system, cap history by count/chars/tokens."""

    max_messages: int = 40
    max_chars: int = 24000
    max_tokens: int = 8000
    keep_system: bool = True
    messages_store: List[dict] = Field(default_factory=list)

    def append(self, role: str, content: Any, **meta: Any) -> dict:
        msg: Dict[str, Any] = {"role": role, "content": content}
        for k, v in meta.items():
            if v is not None:
                msg[k] = v
        self.messages_store.append(msg)
        self.trim()
        return msg

    def add_message(self, msg: dict) -> dict:
        return self.append(
            msg.get("role", "user"),
            msg.get("content", ""),
            **{k: v for k, v in msg.items() if k not in ("role", "content")},
        )

    def add_user(self, content: str) -> dict:
        return self.append("user", content)

    def add_assistant(self, content: str, **meta: Any) -> dict:
        return self.append("assistant", content, **meta)

    def set_system(self, text: str) -> None:
        self.system(text)

    def system(self, text: str) -> dict:
        """Prepend / replace leading system message."""
        if self.messages_store and self.messages_store[0].get("role") == "system":
            self.messages_store[0] = {"role": "system", "content": text}
        else:
            self.messages_store.insert(0, {"role": "system", "content": text})
        return self.messages_store[0]

    def messages(self) -> List[dict]:
        return [dict(m) for m in self.messages_store]

    def clear(self, keep_system: Optional[bool] = None) -> None:
        keep = self.keep_system if keep_system is None else keep_system
        if keep and self.messages_store and self.messages_store[0].get("role") == "system":
            self.messages_store = [self.messages_store[0]]
        else:
            self.messages_store = []

    def token_estimate(self) -> int:
        return estimate_message_tokens(self.messages_store)

    def trim(
        self,
        max_messages: Optional[int] = None,
        max_chars: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> List[dict]:
        """Drop oldest non-system messages until under caps."""
        max_messages = self.max_messages if max_messages is None else max_messages
        max_chars = self.max_chars if max_chars is None else max_chars
        max_tokens = self.max_tokens if max_tokens is None else max_tokens

        def total_chars(msgs: List[dict]) -> int:
            n = 0
            for m in msgs:
                c = m.get("content") or ""
                n += len(str(c))
            return n

        store = self.messages_store
        system = []
        rest = store
        if store and store[0].get("role") == "system":
            system = store[:1]
            rest = store[1:]

        dropped = 0
        while rest and (
            len(system) + len(rest) > max_messages
            or total_chars(system + rest) > max_chars
            or estimate_message_tokens(system + rest) > max_tokens
        ):
            rest.pop(0)
            dropped += 1

        if dropped:
            logger.debug(f"[contextManager] trimmed {dropped} message(s); kept={len(system) + len(rest)}")
        self.messages_store = system + rest
        return self.messages()

    def snapshot(self) -> dict:
        return {
            "count": len(self.messages_store),
            "tokenEstimate": self.token_estimate(),
            "maxMessages": self.max_messages,
            "maxChars": self.max_chars,
            "maxTokens": self.max_tokens,
            "roles": [m.get("role") for m in self.messages_store],
        }

    # camelCase aliases
    def addMessage(self, msg: dict):
        return self.add_message(msg)

    def getMessages(self):
        return self.messages()

    def tokenEstimate(self):
        return self.token_estimate()


DEFAULT_CONTEXT_MANAGER = ContextManager()


def get_context_manager() -> ContextManager:
    return DEFAULT_CONTEXT_MANAGER
