#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/21 11:15
@Author  : Leo Xiao
@File    : anthropic_api.py
@Modified By: mashenquan, 2023/11/21. Add `timeout`.
"""

import anthropic
from anthropic import Anthropic

from metagpt.config import CONFIG


class Claude2:
    def ask(self, prompt, timeout=3):
        client = Anthropic(api_key=CONFIG.claude_api_key)

        res = client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
            timeout=timeout,
        )
        return res.completion

    async def aask(self, prompt, timeout=3):
        client = Anthropic(api_key=CONFIG.claude_api_key)

        res = client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
            timeout=timeout,
        )
        return res.completion
