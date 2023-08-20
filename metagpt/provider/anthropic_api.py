#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/21 11:15
@Author  : Leo Xiao
@File    : anthropic_api.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
"""

import anthropic
from anthropic import Anthropic

from metagpt.config import Config


class Claude2:
    def __init__(self, options=None):
        self.options = options or Config().runtime_options

    def ask(self, prompt):
        client = Anthropic(api_key=self.claude_api_key)

        res = client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
        )
        return res.completion

    async def aask(self, prompt):
        client = Anthropic(api_key=self.claude_api_key)

        res = client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
        )
        return res.completion

    @property
    def claude_api_key(self):
        return self.options.get("claude_api_key")
