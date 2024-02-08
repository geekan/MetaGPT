# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/28
@Author  : mashenquan
@File    : openai.py
@Desc    : mashenquan, 2023/8/28. Separate the `CostManager` class to support user-level cost accounting.
"""

from typing import NamedTuple

from pydantic import BaseModel

from metagpt.logs import logger
from metagpt.utils.token_counter import TOKEN_COSTS


class Costs(NamedTuple):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float
    total_budget: float


class CostManager(BaseModel):
    """Calculate the overhead of using the interface."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_budget: float = 0
    max_budget: float = 10.0
    total_cost: float = 0

    def update_cost(self, prompt_tokens, completion_tokens, model):
        """
        Update the total cost, prompt tokens, and completion tokens.

        Args:
        prompt_tokens (int): The number of tokens used in the prompt.
        completion_tokens (int): The number of tokens used in the completion.
        model (str): The model used for the API call.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        if model not in TOKEN_COSTS:
            logger.warning(f"Model {model} not found in TOKEN_COSTS.")
            return

        cost = (
            prompt_tokens * TOKEN_COSTS[model]["prompt"] + completion_tokens * TOKEN_COSTS[model]["completion"]
        ) / 1000
        self.total_cost += cost
        logger.info(
            f"Total running cost: ${self.total_cost:.3f} | Max budget: ${self.max_budget:.3f} | "
            f"Current cost: ${cost:.3f}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}"
        )

    def get_total_prompt_tokens(self):
        """
        Get the total number of prompt tokens.

        Returns:
        int: The total number of prompt tokens.
        """
        return self.total_prompt_tokens

    def get_total_completion_tokens(self):
        """
        Get the total number of completion tokens.

        Returns:
        int: The total number of completion tokens.
        """
        return self.total_completion_tokens

    def get_total_cost(self):
        """
        Get the total cost of API calls.

        Returns:
        float: The total cost of API calls.
        """
        return self.total_cost

    def get_costs(self) -> Costs:
        """Get all costs"""
        return Costs(self.total_prompt_tokens, self.total_completion_tokens, self.total_cost, self.total_budget)


class TokenCostManager(CostManager):
    """open llm model is self-host, it's free and without cost"""

    def update_cost(self, prompt_tokens, completion_tokens, model):
        """
        Update the total cost, prompt tokens, and completion tokens.

        Args:
        prompt_tokens (int): The number of tokens used in the prompt.
        completion_tokens (int): The number of tokens used in the completion.
        model (str): The model used for the API call.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        logger.info(f"prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}")
