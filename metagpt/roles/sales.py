#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/25 17:21
@Author  : alexanderwu
@File    : sales.py
"""

from typing import Optional

from pydantic import Field

from metagpt.actions import SearchAndSummarize, UserRequirement
from metagpt.document_store.base_store import BaseStore
from metagpt.roles import Role
from metagpt.tools import SearchEngineType


class Sales(Role):
    name: str = "John Smith"
    profile: str = "Retail Sales Guide"
    desc: str = (
        "As a Retail Sales Guide, my name is John Smith. I specialize in addressing customer inquiries with "
        "expertise and precision. My responses are based solely on the information available in our knowledge"
        " base. In instances where your query extends beyond this scope, I'll honestly indicate my inability "
        "to provide an answer, rather than speculate or assume. Please note, each of my replies will be "
        "delivered with the professionalism and courtesy expected of a seasoned sales guide."
    )

    store: Optional[BaseStore] = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_store(self.store)

    def _set_store(self, store):
        if store:
            action = SearchAndSummarize(name="", engine=SearchEngineType.CUSTOM_ENGINE, search_func=store.asearch)
        else:
            action = SearchAndSummarize()
        self._init_actions([action])
        self._watch([UserRequirement])
