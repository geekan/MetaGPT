#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/7/21 11:15
# @Author  : Leo Xiao
# @File    : anthropic_api.py


import anthropic
from anthropic import Anthropic, AsyncAnthropic

from metagpt.configs.llm_config import LLMConfig


class Claude2:
    """A class for interacting with the Claude2 model via the Anthropic API.

    This class provides synchronous and asynchronous methods to query the Claude2 model.

    Attributes:
        config: A configuration object containing the API key and other settings.
    """

    def __init__(self, config: LLMConfig):
        """Initializes the Claude2 object with the given configuration.

        Args:
            config: A configuration object containing the API key and other settings.
        """
        self.config = config

    def ask(self, prompt: str) -> str:
        """Sends a synchronous request to the Claude2 model.

        Args:
            prompt: The input prompt for the model.

        Returns:
            The model's response as a string.
        """
        client = Anthropic(api_key=self.config.api_key)

        res = client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
        )
        return res.completion

    async def aask(self, prompt: str) -> str:
        """Sends an asynchronous request to the Claude2 model.

        Args:
            prompt: The input prompt for the model.

        Returns:
            The model's response as a string.
        """
        aclient = AsyncAnthropic(api_key=self.config.api_key)

        res = await aclient.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
        )
        return res.completion
