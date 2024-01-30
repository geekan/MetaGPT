#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/26 14:27
@Author  : zhanglei
@File    : moderation.py
"""
from typing import Union

from metagpt.provider.base_llm import BaseLLM


class Moderation:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def handle_moderation_results(self, results):
        resp = []
        for item in results:
            categories = item.categories.dict()
            true_categories = [category for category, item_flagged in categories.items() if item_flagged]
            resp.append({"flagged": item.flagged, "true_categories": true_categories})
        return resp

    async def amoderation_with_categories(self, content: Union[str, list[str]]):
        resp = []
        if content:
            moderation_results = await self.llm.amoderation(content=content)
            resp = self.handle_moderation_results(moderation_results.results)
        return resp

    async def amoderation(self, content: Union[str, list[str]]):
        resp = []
        if content:
            moderation_results = await self.llm.amoderation(content=content)
            results = moderation_results.results
            for item in results:
                resp.append(item.flagged)

        return resp
