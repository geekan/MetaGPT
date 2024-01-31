#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/21 11:15
@Author  : Leo Xiao
@File    : anthropic_api.py
"""

import anthropic
from anthropic import Anthropic, AsyncAnthropic

from metagpt.configs.llm_config import LLMConfig


class Claude2:
    def __init__(self, config: LLMConfig):
        self.config = config

    def ask(self, prompt: str) -> str:
        client = Anthropic(api_key=self.config.api_key)

        res = client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
        )
        return res.completion

    async def aask(self, prompt: str) -> str:
        aclient = AsyncAnthropic(api_key=self.config.api_key)

        res = await aclient.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
        )
        return res.completion
