#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/21 11:15
@Author  : Leo Xiao
@File    : anthropic_api.py
"""

import anthropic
from anthropic import Anthropic, AsyncAnthropic
from metagpt.config import CONFIG


class Claude2:
    def ask(self, prompt):
        client = Anthropic(api_key=CONFIG.claude_api_key)

        res = client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=8192,
        )
        return res.completion

    async def aask(self, prompt):
        client = AsyncAnthropic(api_key=CONFIG.claude_api_key)
        res = await client.completions.create(
            model="claude-2",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            max_tokens_to_sample=8192,
        )
        return res.completion
    
    async def async_stream(self, prompt):
        collected_messages = []
        client = AsyncAnthropic(api_key=CONFIG.claude_api_key)
        stream = await client.completions.create(
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            model="claude-2",
            stream=True,
            max_tokens_to_sample=300,
        )

        async for completion in stream:
            print(completion.completion, end="")
            collected_messages.append(completion.completion)

        print()
        full_reply_content = ''.join(collected_messages)
        # prompt_token = self.sync_tokens(prompt)
        # completion_token = self.sync_tokens(completion.completion)
        return full_reply_content
    
    def sync_tokens(self, text):
        client = Anthropic()
        tokens = client.count_tokens(text)
        return tokens



    async def async_tokens(self, text):
        anthropic = AsyncAnthropic()
        tokens = await anthropic.count_tokens(text)
        return tokens

