#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for circuit breaker + FallbackLLM (no real network)."""

import asyncio
import unittest
from unittest.mock import patch

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.circuit_breaker import (
    CircuitOpenError,
    CircuitState,
    assert_allowed,
    circuit_breaker_status,
    get_circuit_breaker,
    reset_circuit_breaker,
)
from metagpt.provider.fallback_router import FallbackLLM
from metagpt.provider.task_chains import (
    DEFAULT_TASK_CHAINS,
    build_provider_chain,
    build_task_chain,
    is_provider_configured,
)


class FakeLLM(BaseLLM):
    """Controllable stub provider."""

    def __init__(self, config: LLMConfig, fail_times: int = 0, label: str = "fake"):
        self.config = config
        self.model = config.model
        self.label = label
        self.fail_times = fail_times
        self.calls = 0
        self.cost_manager = None
        self.use_system_prompt = True
        self.system_prompt = "You are a helpful assistant."
        self.aclient = None
        self._reasoning_content = None

    async def _achat_completion(self, messages, timeout=600):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"{self.label} boom")
        return {"choices": [{"message": {"content": f"ok-from-{self.label}"}}]}

    async def acompletion(self, messages, timeout=600):
        return await self._achat_completion(messages, timeout)

    async def _achat_completion_stream(self, messages, timeout=600) -> str:
        return await self._achat_completion(messages, timeout)

    def get_choice_text(self, rsp: dict) -> str:
        return rsp["choices"][0]["message"]["content"]


def _cfg(api_type=LLMType.OPENAI, model="m1", **kw):
    data = dict(api_type=api_type, model=model, api_key="sk-test", base_url="http://localhost")
    data.update(kw)
    return LLMConfig(**data)


class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        reset_circuit_breaker()

    def test_opens_after_threshold(self):
        b = get_circuit_breaker("t1", threshold=3, reset_timeout=60)
        for _ in range(3):
            self.assertTrue(b.allow_request())
            b.record_failure()
        self.assertEqual(b.state, CircuitState.OPEN)
        self.assertFalse(b.allow_request())

    def test_half_open_then_close(self):
        b = get_circuit_breaker("t2", threshold=1, reset_timeout=0.0)
        b.record_failure()
        self.assertEqual(b.state, CircuitState.OPEN)
        self.assertTrue(b.allow_request())  # transitions to half_open
        b.record_success()
        self.assertEqual(b.state, CircuitState.CLOSED)


class TestBuildTaskChain(unittest.TestCase):
    def test_primary_first_dedup(self):
        chain = build_task_chain("gpt-4o-mini", ["gemini", "openai"], task="code", filter_unconfigured=False)
        self.assertEqual(chain[0], "gpt-4o-mini")
        self.assertEqual(len(chain), len(set(chain)))
        self.assertIn("gemini", chain)

    def test_env_filter_skips_unconfigured(self):
        env = {"OPENAI_API_KEY": "sk-test"}
        chain = build_task_chain("openai", task="json", env=env)
        self.assertEqual(chain[0], "openai")
        # gemini/deepseek have no key → filtered
        self.assertNotIn("gemini", chain)
        self.assertNotIn("deepseek", chain)
        self.assertIn("ollama", chain)  # local always allowed

    def test_is_provider_configured(self):
        self.assertTrue(is_provider_configured("ollama", env={}))
        self.assertTrue(is_provider_configured("openai", env={"OPENAI_API_KEY": "x"}))
        self.assertFalse(is_provider_configured("openai", env={}))

    def test_build_provider_chain_ends_with_mock(self):
        chain = build_provider_chain("openai", task_type="chat", env={"OPENAI_API_KEY": "x"})
        self.assertEqual(chain[0], "openai")
        self.assertEqual(chain[-1], "mock")

    def test_default_task_chains_tasks(self):
        for t in ("code", "json", "chat", "creative", "translate", "default"):
            self.assertTrue(DEFAULT_TASK_CHAINS[t])

    def test_circuit_open_error_shared_code(self):
        reset_circuit_breaker()
        b = get_circuit_breaker("t-code", threshold=1)
        b.record_failure()
        with self.assertRaises(CircuitOpenError) as ctx:
            assert_allowed("t-code")
        self.assertEqual(ctx.exception.code, "CIRCUIT_OPEN")


class TestFallbackLLM(unittest.TestCase):
    def setUp(self):
        reset_circuit_breaker()

    def test_failover_to_second_provider(self):
        primary = FakeLLM(_cfg(model="primary"), fail_times=99, label="primary")
        secondary = FakeLLM(_cfg(model="secondary"), label="secondary")

        cfg = _cfg(model="primary", enable_resilience=True, stream=False)
        with patch.object(FallbackLLM, "_init_providers", lambda self: None):
            llm = FallbackLLM(cfg)
        llm.providers = [primary, secondary]
        llm._provider_keys = ["primary", "secondary"]

        text = asyncio.run(llm.acompletion_text([{"role": "user", "content": "hi"}], stream=False))
        self.assertEqual(text, "ok-from-secondary")
        self.assertGreaterEqual(primary.calls, 1)
        self.assertGreaterEqual(secondary.calls, 1)

    def test_all_fail_raises(self):
        primary = FakeLLM(_cfg(model="primary"), fail_times=99, label="primary")
        secondary = FakeLLM(_cfg(model="secondary"), fail_times=99, label="secondary")

        cfg = _cfg(model="primary", enable_resilience=True, stream=False)
        with patch.object(FallbackLLM, "_init_providers", lambda self: None):
            llm = FallbackLLM(cfg)
        llm.providers = [primary, secondary]
        llm._provider_keys = ["primary", "secondary"]

        with self.assertRaises(RuntimeError):
            asyncio.run(llm.acompletion_text([{"role": "user", "content": "hi"}], stream=False))

    def test_circuit_opens_and_skips(self):
        reset_circuit_breaker()
        primary = FakeLLM(_cfg(model="primary"), fail_times=99, label="primary")

        cfg = _cfg(model="primary", enable_resilience=True, circuit_breaker_threshold=2, stream=False)
        with patch.object(FallbackLLM, "_init_providers", lambda self: None):
            llm = FallbackLLM(cfg)
        llm.providers = [primary]
        llm._provider_keys = ["primary"]

        msgs = [{"role": "user", "content": "hi"}]
        for _ in range(4):
            try:
                asyncio.run(llm.acompletion_text(msgs, stream=False))
            except Exception:
                pass

        status = circuit_breaker_status()
        self.assertTrue(any(v["state"] == "open" for v in status.values()))


if __name__ == "__main__":
    unittest.main()
