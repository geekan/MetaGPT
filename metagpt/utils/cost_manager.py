# -*- coding: utf-8 -*-
"""
CostManager — shared cost-accounting interface (aligned with MEO-AI server/ai/costManager.js).

Shared contract (both languages):
  updateCost({promptTokens, completionTokens, totalTokens, model, provider}) -> charge dict
  checkBudget()   -> raise NoMoneyError when enforce && totalCost >= maxBudget
  getCosts()      -> { totalPromptTokens, totalCompletionTokens, totalCost, maxBudget,
                       remaining, overBudget, blocked, enforceBudget }
  setBudget(maxBudget, {enforce}) -> getCosts()
  reset()         -> getCosts()
  snapshot()      -> getCosts() + byModel + byProvider

Also keeps MetaGPT snake_case API used by BaseLLM / Team:
  update_cost(prompt_tokens, completion_tokens, model)
  get_costs() -> Costs NamedTuple (legacy)
"""

from __future__ import annotations

import re
from typing import Any, Dict, NamedTuple, Optional

from pydantic import BaseModel, Field

from metagpt.logs import logger
from metagpt.utils.token_counter import FIREWORKS_GRADE_TOKEN_COSTS, TOKEN_COSTS

# Shared error code with MEO costManager.js
NO_MONEY = "NO_MONEY"


class Costs(NamedTuple):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float
    total_budget: float


class NoMoneyError(RuntimeError):
    """Budget exceeded — same code as MEO NoMoneyError."""

    def __init__(self, total_cost: float, max_budget: float):
        self.total_cost = float(total_cost)
        self.max_budget = float(max_budget)
        self.code = NO_MONEY
        super().__init__(
            f"Insufficient AI budget: spent ${self.total_cost:.4f} >= max ${self.max_budget:.4f}"
        )


def resolve_token_costs(model: Optional[str], token_costs: Optional[dict] = None) -> Optional[dict]:
    """Fuzzy-match model id to pricing row (exact → prefix → contains), like MEO."""
    if not model:
        return None
    table = token_costs or TOKEN_COSTS
    key = str(model).lower()
    if key in table:
        return table[key]
    if model in table:
        return table[model]

    best = None
    best_len = 0
    for name, costs in table.items():
        n = name.lower()
        if key.startswith(n) or n.startswith(key) or key in n or n in key:
            if len(n) > best_len:
                best = costs
                best_len = len(n)
    return best


class CostManager(BaseModel):
    """Calculate LLM overhead. Shared interface with MEO CostManager."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_budget: float = 0
    max_budget: float = 10.0
    total_cost: float = 0
    enforce_budget: bool = False
    blocked: bool = False
    token_costs: dict[str, dict[str, float]] = Field(default_factory=lambda: dict(TOKEN_COSTS))
    by_model: dict[str, dict[str, float]] = Field(default_factory=dict)
    by_provider: dict[str, dict[str, float]] = Field(default_factory=dict)

    # ── Shared camelCase API (MEO-compatible) ──────────────────────────

    def updateCost(
        self,
        promptTokens: int = 0,
        completionTokens: int = 0,
        totalTokens: int = 0,
        model: str = "",
        provider: str = "",
        **_ignored: Any,
    ) -> dict:
        pt = int(promptTokens or 0)
        ct = int(completionTokens or 0)
        if not pt and not ct and totalTokens:
            ct = int(totalTokens or 0)
        if pt + ct == 0:
            return {"promptTokens": 0, "completionTokens": 0, "cost": 0.0, "totalCost": self.total_cost}

        self.total_prompt_tokens += pt
        self.total_completion_tokens += ct

        rates = resolve_token_costs(model, self.token_costs)
        if rates is None:
            logger.warning(f"[costManager] no pricing for model '{model}', cost=0 (tokens still counted)")
            cost = 0.0
        else:
            cost = (pt * float(rates.get("prompt", 0)) + ct * float(rates.get("completion", 0))) / 1000.0

        self.total_cost += cost
        m = model or "unknown"
        mc = self.by_model.setdefault(m, {"tokens": 0.0, "cost": 0.0, "calls": 0.0})
        mc["tokens"] += pt + ct
        mc["cost"] += cost
        mc["calls"] += 1

        if provider:
            pc = self.by_provider.setdefault(provider, {"tokens": 0.0, "cost": 0.0, "calls": 0.0})
            pc["tokens"] += pt + ct
            pc["cost"] += cost
            pc["calls"] += 1

        logger.info(
            f"Total running cost: ${self.total_cost:.4f} | Max budget: ${self.max_budget:.4f} | "
            f"Current cost: ${cost:.6f}, model={model}, prompt_tokens={pt}, completion_tokens={ct}"
        )
        return {
            "promptTokens": pt,
            "completionTokens": ct,
            "cost": cost,
            "totalCost": self.total_cost,
        }

    def checkBudget(self) -> bool:
        if self.blocked:
            raise NoMoneyError(self.total_cost, self.max_budget)
        if self.enforce_budget and self.total_cost >= self.max_budget:
            self.blocked = True
            raise NoMoneyError(self.total_cost, self.max_budget)
        return True

    def getCosts(self) -> dict:
        return {
            "totalPromptTokens": self.total_prompt_tokens,
            "totalCompletionTokens": self.total_completion_tokens,
            "totalCost": self.total_cost,
            "totalBudget": self.max_budget,
            "maxBudget": self.max_budget,
            "enforceBudget": self.enforce_budget,
            "overBudget": self.total_cost >= self.max_budget,
            "blocked": self.blocked,
            "remaining": max(0.0, self.max_budget - self.total_cost),
        }

    def setBudget(self, maxBudget: float, enforce: Optional[bool] = None) -> dict:
        self.max_budget = float(maxBudget)
        if enforce is not None:
            self.enforce_budget = bool(enforce)
        if self.total_cost < self.max_budget:
            self.blocked = False
        return self.getCosts()

    def snapshot(self) -> dict:
        return {
            **self.getCosts(),
            "byModel": {k: dict(v) for k, v in self.by_model.items()},
            "byProvider": {k: dict(v) for k, v in self.by_provider.items()},
        }

    def reset(self) -> dict:
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0
        self.blocked = False
        self.by_model = {}
        self.by_provider = {}
        return self.getCosts()

    # ── MetaGPT snake_case API (legacy) ────────────────────────────────

    def update_cost(self, prompt_tokens, completion_tokens, model, provider: str = ""):
        """
        Update the total cost, prompt tokens, and completion tokens.
        """
        if prompt_tokens + completion_tokens == 0 or not model:
            return
        self.updateCost(
            promptTokens=prompt_tokens,
            completionTokens=completion_tokens,
            model=model,
            provider=provider,
        )

    def check_budget(self) -> bool:
        return self.checkBudget()

    def get_total_prompt_tokens(self):
        return self.total_prompt_tokens

    def get_total_completion_tokens(self):
        return self.total_completion_tokens

    def get_total_cost(self):
        return self.total_cost

    def get_costs(self) -> Costs:
        """Legacy Costs tuple for BaseLLM.get_costs() / Team."""
        return Costs(self.total_prompt_tokens, self.total_completion_tokens, self.total_cost, self.max_budget)


class TokenCostManager(CostManager):
    """open llm model is self-host, it's free and without cost"""

    def update_cost(self, prompt_tokens, completion_tokens, model, provider: str = ""):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        logger.info(f"prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}")


class FireworksCostManager(CostManager):
    def model_grade_token_costs(self, model: str) -> dict[str, float]:
        def _get_model_size(model: str) -> float:
            size = re.findall(".*-([0-9.]+)b", model)
            size = float(size[0]) if len(size) > 0 else -1
            return size

        if "mixtral-8x7b" in model:
            token_costs = FIREWORKS_GRADE_TOKEN_COSTS["mixtral-8x7b"]
        else:
            model_size = _get_model_size(model)
            if 0 < model_size <= 16:
                token_costs = FIREWORKS_GRADE_TOKEN_COSTS["16"]
            elif 16 < model_size <= 80:
                token_costs = FIREWORKS_GRADE_TOKEN_COSTS["80"]
            else:
                token_costs = FIREWORKS_GRADE_TOKEN_COSTS["-1"]
        return token_costs

    def update_cost(self, prompt_tokens: int, completion_tokens: int, model: str, provider: str = ""):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        token_costs = self.model_grade_token_costs(model)
        cost = (prompt_tokens * token_costs["prompt"] + completion_tokens * token_costs["completion"]) / 1000000
        self.total_cost += cost
        logger.info(
            f"Total running cost: ${self.total_cost:.4f}, "
            f"Current cost: ${cost:.4f}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}"
        )
