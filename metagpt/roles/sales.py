#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/25 17:21
# @Author  : alexanderwu
# @File    : sales.py


from typing import Optional

from pydantic import Field, model_validator

from metagpt.actions import SearchAndSummarize, UserRequirement
from metagpt.document_store.base_store import BaseStore
from metagpt.roles import Role
from metagpt.tools.search_engine import SearchEngine


class Sales(Role):
    """Represents a Sales role with specific attributes and behaviors.

    This class extends the Role class, specializing it for the context of retail sales. It includes
    attributes for the salesperson's name, profile, and description, as well as the ability to interact
    with a knowledge base store for retrieving information.

    Attributes:
        name: A string representing the salesperson's name.
        profile: A string representing the salesperson's profile.
        desc: A detailed string describing the salesperson's role and approach to customer service.
        store: An optional BaseStore object representing the knowledge base store.
    """

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

    @model_validator(mode="after")
    def validate_stroe(self):
        if self.store:
            search_engine = SearchEngine.from_search_func(search_func=self.store.asearch, proxy=self.config.proxy)
            action = SearchAndSummarize(search_engine=search_engine, context=self.context)
        else:
            action = SearchAndSummarize
        self.set_actions([action])
        self._watch([UserRequirement])
        return self
