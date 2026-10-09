#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Task-aware provider fallback chains — MetaGPT twin of MEO server/ai/taskChains.js.

Pure functions — no network, no health checks.
"""

from __future__ import annotations

import os
from typing import Dict, List, Mapping, Optional, Sequence

# Task → preferred api_type / model-key order (primary is always tried first).
# Values may be LLMType values or ModelsConfig keys.
DEFAULT_TASK_CHAINS: Dict[str, List[str]] = {
    "code": ["openai", "gemini", "deepseek", "ollama"],
    "creative": ["openai", "anthropic", "gemini", "ollama"],
    "json": ["openai", "gemini", "deepseek", "ollama"],
    "chat": ["openai", "gemini", "anthropic", "ollama"],
    "translate": ["openai", "gemini", "ollama"],
    "quick": ["openai", "gemini", "deepseek", "ollama"],
    "general": ["openai", "gemini", "deepseek", "anthropic", "ollama"],
    "default": ["openai", "gemini", "deepseek", "anthropic", "ollama"],
}

# Env keys required for a cloud provider to be eligible (MEO isProviderConfigured).
_PROVIDER_ENV_KEYS: Dict[str, List[str]] = {
    "openai": ["OPENAI_API_KEY"],
    "gemini": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "azure": ["AZURE_OPENAI_API_KEY"],
    "zhipuai": ["ZHIPUAI_API_KEY"],
    "qianfan": ["QIANFAN_API_KEY"],
    "dashscope": ["DASHSCOPE_API_KEY"],
}


def is_provider_configured(provider: str, env: Optional[Mapping[str, str]] = None) -> bool:
    """True if provider has required env credentials (or needs none)."""
    env = os.environ if env is None else env
    keys = _PROVIDER_ENV_KEYS.get(provider)
    if not keys:
        # ollama / local / unknown — allow; availability is health-check territory
        return True
    return any(env.get(k) for k in keys)


def build_task_chain(
    primary_key: str,
    fallback_keys: Sequence[str] = (),
    task: str = "default",
    env: Optional[Mapping[str, str]] = None,
    filter_unconfigured: bool = True,
) -> List[str]:
    """Primary first, then configured fallbacks, then task defaults (deduped).

    Mirrors MEO buildFallbackChain + buildTaskChain semantics.
    """
    chain: List[str] = [primary_key] if primary_key else []
    extras = list(fallback_keys) + list(DEFAULT_TASK_CHAINS.get(task, DEFAULT_TASK_CHAINS["default"]))
    for key in extras:
        if not key or key in chain:
            continue
        if filter_unconfigured and not is_provider_configured(key, env=env):
            continue
        chain.append(key)
    return chain


def build_provider_chain(
    primary_provider: Optional[str],
    fallback_provider: Optional[str] = None,
    task_type: str = "default",
    env: Optional[Mapping[str, str]] = None,
    always_mock: bool = True,
) -> List[str]:
    """MEO-style chain: primary → task defaults → explicit fallback → optional mock."""
    chain = build_task_chain(
        primary_key=primary_provider or "",
        fallback_keys=[fallback_provider] if fallback_provider else [],
        task=task_type,
        env=env,
        filter_unconfigured=True,
    )
    if not primary_provider and not chain:
        chain = [k for k in DEFAULT_TASK_CHAINS.get(task_type, DEFAULT_TASK_CHAINS["default"]) if is_provider_configured(k, env)]
    if always_mock and "mock" not in chain:
        chain.append("mock")
    return chain
