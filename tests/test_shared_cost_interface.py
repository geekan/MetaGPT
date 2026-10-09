#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Shared CostManager interface tests — must match MEO costManager.js semantics."""

import asyncio
import unittest

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.base_llm import BaseLLM
from metagpt.utils.cost_manager import CostManager, NoMoneyError, resolve_token_costs


def _cfg(**kw):
    data = dict(api_type=LLMType.OPENAI, model="gpt-4o-mini", api_key="sk-test", base_url="http://localhost")
    data.update(kw)
    return LLMConfig(**data)


class FakeProvider(BaseLLM):
    def __init__(self, config: LLMConfig, fail_budget: bool = False):
        self.config = config
        self.model = config.model
        self.cost_manager = None
        self.use_system_prompt = True
        self.system_prompt = "sys"
        self.aclient = None
        self._reasoning_content = None
        self.calls = 0
        self._fail_budget = fail_budget

    async def _achat_completion(self, messages, timeout=600):
        self.calls += 1
        # simulate usage accounting like OpenAILLM
        usage = {"prompt_tokens": 1000, "completion_tokens": 1000}
        self._update_costs(usage, model=self.model, provider="openai")
        return {"choices": [{"message": {"content": "ok"}}]}

    async def acompletion(self, messages, timeout=600):
        return await self._achat_completion(messages, timeout)

    async def _achat_completion_stream(self, messages, timeout=600) -> str:
        return await self._achat_completion(messages, timeout)

    def get_choice_text(self, rsp: dict) -> str:
        return rsp["choices"][0]["message"]["content"]


class TestSharedCostInterface(unittest.TestCase):
    def test_resolve_token_costs_fuzzy(self):
        self.assertEqual(resolve_token_costs("gpt-4o-mini")["prompt"], 0.00015)
        self.assertIsNotNone(resolve_token_costs("gpt-4o-mini-2024-07-18"))

    def test_update_cost_shared_shape(self):
        cm = CostManager()
        r = cm.updateCost(promptTokens=1000, completionTokens=1000, model="gpt-4o-mini", provider="openai")
        self.assertAlmostEqual(r["cost"], 0.00075, places=10)
        self.assertIn("totalCost", r)
        snap = cm.getCosts()
        for k in ("totalPromptTokens", "totalCompletionTokens", "totalCost", "maxBudget", "remaining", "overBudget", "blocked"):
            self.assertIn(k, snap)

    def test_total_tokens_fallback(self):
        cm = CostManager()
        cm.updateCost(totalTokens=500, model="gpt-4o-mini")
        self.assertEqual(cm.total_completion_tokens, 500)

    def test_no_money_error_code(self):
        cm = CostManager(max_budget=0.0001, enforce_budget=True)
        cm.updateCost(promptTokens=100000, completionTokens=100000, model="gpt-4o")
        with self.assertRaises(NoMoneyError) as ctx:
            cm.checkBudget()
        self.assertEqual(ctx.exception.code, "NO_MONEY")

    def test_snake_case_aliases(self):
        cm = CostManager()
        cm.update_cost(1000, 1000, "gpt-4o-mini", provider="openai")
        self.assertGreater(cm.total_cost, 0)
        self.assertTrue(cm.check_budget())
        costs = cm.get_costs()
        self.assertEqual(costs.total_prompt_tokens, 1000)

    def test_basellm_budget_gate(self):
        cfg = _cfg(model="gpt-4o", enforce_budget=True, max_budget=0.0001)
        llm = FakeProvider(cfg)
        llm.cost_manager = CostManager(max_budget=0.0001, enforce_budget=True)
        # first call charges ~$0.2 for gpt-4o 10k+10k
        asyncio.run(llm.acompletion_text([{"role": "user", "content": "hi"}], stream=False))
        with self.assertRaises(NoMoneyError):
            asyncio.run(llm.acompletion_text([{"role": "user", "content": "hi"}], stream=False))

    def test_basellm_set_budget_and_snapshot(self):
        cfg = _cfg()
        llm = FakeProvider(cfg)
        llm.cost_manager = CostManager()
        snap = llm.set_budget(5.0, enforce=False)
        self.assertEqual(snap["maxBudget"], 5.0)
        asyncio.run(llm.acompletion_text([{"role": "user", "content": "x"}], stream=False))
        snapshot = llm.get_cost_snapshot()
        self.assertGreater(snapshot["totalPromptTokens"], 0)
        self.assertGreater(snapshot["totalCost"], 0)

    def test_basellm_update_costs_via_updateCost(self):
        cfg = _cfg()
        llm = FakeProvider(cfg)
        llm.cost_manager = CostManager()
        asyncio.run(llm.acompletion_text([{"role": "user", "content": "x"}], stream=False))
        self.assertIn("openai", llm.cost_manager.by_provider)
        self.assertIn("gpt-4o-mini", llm.cost_manager.by_model)


if __name__ == "__main__":
    unittest.main()
