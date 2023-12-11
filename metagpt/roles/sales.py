#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/25 17:21
@Author  : alexanderwu
@File    : sales.py
"""
from metagpt.actions import SearchAndSummarize
from metagpt.roles import Role
from metagpt.tools import SearchEngineType


class Sales(Role):
    def __init__(
        self,
        name="Xiaomei",
        profile="Retail sales guide",
        desc="I am a sales guide in retail. My name is Xiaomei. I will answer some customer questions next, and I "
        "will answer questions only based on the information in the knowledge base."
        "If I feel that you can't get the answer from the reference material, then I will directly reply that"
        " I don't know, and I won't tell you that this is from the knowledge base,"
        "but pretend to be what I know. Note that each of my replies will be replied in the tone of a "
        "professional guide",
        store=None,
    ):
        super().__init__(name, profile, desc=desc)
        self._set_store(store)

    def _set_store(self, store):
        if store:
            action = SearchAndSummarize("", engine=SearchEngineType.CUSTOM_ENGINE, search_func=store.asearch)
        else:
            action = SearchAndSummarize()
        self._init_actions([action])
