#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Task-aware multi-provider fallback router for MetaGPT (MEO FallbackLLM twin).

Task chains + env filter live in metagpt/provider/task_chains.py (MEO taskChains.js).
Circuit breaker lives in metagpt/provider/circuit_breaker.py (MEO circuitBreaker.js).
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Sequence

from metagpt.configs.llm_config import LLMConfig
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.circuit_breaker import CircuitOpenError, get_circuit_breaker
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.provider.rate_limiter import get_rate_limiter
from metagpt.provider.retry_policy import DEFAULT_RETRY_POLICY, with_retry
from metagpt.provider.task_chains import DEFAULT_TASK_CHAINS, build_task_chain, is_provider_configured

# Re-export for backward compatibility (imported from fallback_router in T1)
__all__ = ["FallbackLLM", "build_task_chain", "DEFAULT_TASK_CHAINS", "is_provider_configured"]

_RETRY_MAX = 1  # extra attempts per provider (on top of the first)
_RETRY_BASE_DELAY = 0.5


class FallbackLLM(BaseLLM):
    """Route aask/acompletion through a circuit-broken provider chain.

    The primary config is the first hop. Extra hops come from
    `LLMConfig.fallback_models` (ModelsConfig keys) and task defaults.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = config.model
        self.pricing_plan = config.pricing_plan or config.model
        self.system_prompt = config.system_prompt if hasattr(config, "system_prompt") else "You are a helpful assistant."
        self.use_system_prompt = config.use_system_prompt
        self.cost_manager = None
        self._reasoning_content = None
        self.providers: List[BaseLLM] = []
        self._provider_keys: List[str] = []
        self._init_providers()
        # Expose primary as .aclient-compatible surface for debugging
        self.aclient = getattr(self.providers[0] if self.providers else None, "aclient", None)

    def _init_providers(self) -> None:
        from metagpt.configs.models_config import ModelsConfig

        models_cfg = ModelsConfig.default().models
        keys = build_task_chain(
            primary_key=self.config.model or self.config.api_type.value,
            fallback_keys=self.config.fallback_models or [],
            task=self.config.default_task or "default",
        )
        seen_cfgs = set()
        for key in keys:
            cfg = self._resolve_config(key, models_cfg)
            if cfg is None:
                continue
            sig = (cfg.api_type, cfg.model, cfg.base_url, cfg.api_key)
            if sig in seen_cfgs:
                continue
            seen_cfgs.add(sig)
            try:
                # Never wrap children with FallbackLLM again (avoid recursion)
                child_cfg = cfg.model_copy(update={"enable_resilience": False})
                child = create_llm_instance(child_cfg)
            except Exception as e:
                logger.warning(f"[fallback] skip provider '{key}': {e}")
                continue
            if self.cost_manager is not None:
                child.cost_manager = self.cost_manager
            self.providers.append(child)
            self._provider_keys.append(key)
        if not self.providers:
            # Always keep primary so we still behave like a normal LLM
            primary = create_llm_instance(self.config.model_copy(update={"enable_resilience": False}))
            self.providers.append(primary)
            self._provider_keys.append(self.config.model or "primary")
        logger.info(f"[fallback] chain: {' -> '.join(self._provider_keys)}")

    def _resolve_config(self, key: str, models_cfg: Dict[str, LLMConfig]) -> Optional[LLMConfig]:
        if key in (self.config.model, self.config.api_type.value, self.config.api_type.name):
            return self.config
        if key in models_cfg:
            return models_cfg[key]
        # match by api_type among models
        for m in models_cfg.values():
            if m.api_type.value == key or m.api_type.name == key:
                return m
        return None

    def set_cost_manager(self, cost_manager) -> None:
        self.cost_manager = cost_manager
        for p in self.providers:
            p.cost_manager = cost_manager

    # --- BaseLLM abstract surface (delegate to primary for unused paths) ---

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT):
        return await self.providers[0]._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def acompletion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT):
        return await self.providers[0].acompletion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        # Streaming stays on primary only (no mid-stream provider switch)
        return await self.providers[0]._achat_completion_stream(messages, timeout=self.get_timeout(timeout))

    def get_choice_text(self, rsp: dict) -> str:
        return self.providers[0].get_choice_text(rsp)

    # --- Resilient text path ---

    async def acompletion_text(
        self,
        messages: list[dict],
        stream: bool = False,
        timeout: int = USE_CONFIG_TIMEOUT,
        task: Optional[str] = None,
    ) -> str:
        """Try providers in task-aware order with per-provider circuit breaker."""
        self.check_budget()
        task_name = task or self.config.default_task or "default"
        chain = self._chain_for_task(task_name)
        last_error: Optional[Exception] = None

        for key, provider in chain:
            breaker_name = f"metagpt:{key}"
            breaker = get_circuit_breaker(
                breaker_name,
                threshold=self.config.circuit_breaker_threshold,
                reset_timeout=self.config.circuit_breaker_reset_timeout,
            )
            if not breaker.allow_request():
                logger.warning(f"[fallback] circuit OPEN, skip {key}")
                last_error = CircuitOpenError(breaker_name, breaker.failures)
                continue

            try:
                if stream:
                    call = lambda p=provider: p._achat_completion_stream(  # noqa: E731
                        messages, timeout=self.get_timeout(timeout)
                    )
                else:
                    call = lambda p=provider: p.acompletion_text(  # noqa: E731
                        messages, stream=False, timeout=self.get_timeout(timeout)
                    )
                text = await self._call_with_retry(call, breaker, provider_key=key)
                if key != self._provider_keys[0]:
                    logger.info(f"[fallback] succeeded via {key} (primary={self._provider_keys[0]}, task={task_name})")
                return text
            except CircuitOpenError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                logger.warning(f"[fallback] provider {key} failed: {e}")
                continue

        raise RuntimeError(
            f"All providers failed for task={task_name}: {[k for k, _ in chain]}; last_error={last_error}"
        ) from last_error

    def _chain_for_task(self, task: str) -> List[tuple[str, BaseLLM]]:
        """Configured providers first (init order), then task defaults by api_type."""
        ordered: List[tuple[str, BaseLLM]] = list(zip(self._provider_keys, self.providers))
        result: List[tuple[str, BaseLLM]] = []
        seen = set()
        for key, provider in ordered:
            if id(provider) not in seen:
                result.append((key, provider))
                seen.add(id(provider))
        for pref in DEFAULT_TASK_CHAINS.get(task, DEFAULT_TASK_CHAINS["default"]):
            for key, provider in ordered:
                if provider.config.api_type.value == pref and id(provider) not in seen:
                    result.append((key, provider))
                    seen.add(id(provider))
        return result

    async def _call_with_retry(self, call_factory, breaker, provider_key: str = "") -> str:
        """Retry with shared RetryPolicy; record success/failure on circuit breaker."""
        limiter = get_rate_limiter()
        rkey = f"metagpt:{provider_key}" if provider_key else "metagpt:fallback"
        gate = await limiter.acquire(rkey)
        try:
            async def _attempt():
                try:
                    text = await call_factory()
                    breaker.record_success()
                    return text
                except Exception as e:
                    breaker.record_failure()
                    raise

            return await with_retry(_attempt, policy=DEFAULT_RETRY_POLICY)
        finally:
            if gate.get("allowed"):
                limiter.release(rkey)

    async def aask(
        self,
        msg,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        images=None,
        timeout=USE_CONFIG_TIMEOUT,
        stream=None,
        task: Optional[str] = None,
    ) -> str:
        if system_msgs:
            message = self._system_msgs(system_msgs)
        else:
            message = [self._default_system_msg()]
        if not self.use_system_prompt:
            message = []
        if format_msgs:
            message.extend(format_msgs)
        if isinstance(msg, str):
            message.append(self._user_msg(msg, images=images))
        else:
            message.extend(msg)
        if stream is None:
            stream = self.config.stream

        masked = [self.mask_base64_data(m) for m in message]
        logger.debug(masked)
        compressed = self.compress_messages(message, compress_type=self.config.compress_type)
        return await self.acompletion_text(
            compressed, stream=stream, timeout=self.get_timeout(timeout), task=task
        )

    @property
    def reasoning_content(self):
        return self._reasoning_content

    @reasoning_content.setter
    def reasoning_content(self, value: str):
        self._reasoning_content = value
        # propagate if primary supports it
        if self.providers:
            self.providers[0].reasoning_content = value

    def with_model(self, model: str):
        self.model = model
        if self.providers:
            self.providers[0].with_model(model)
        return self
