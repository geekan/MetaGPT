#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/21 11:15
@Author  : Leo Xiao
@File    : anthropic_api.py
"""

import asyncio
import anthropic
from anthropic import Anthropic
from metagpt.config import CONFIG

class Claude2:
    def ask(self, prompt):
        client = Anthropic(api_key=claude_api_key)

        res = client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
        )
        return res.completion
    
    async def aask(self, prompt):
            client = Anthropic(api_key="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")

            res = client.completions.create(
                model="claude-2",
                prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
                max_tokens_to_sample=1000,
            )
            return res.completion

