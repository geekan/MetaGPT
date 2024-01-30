#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 19:06
# @Author  : alexanderwu
# @File    : search_config.py

from metagpt.tools import SearchEngineType
from metagpt.utils.yaml_model import YamlModel


class SearchConfig(YamlModel):
    """Config for Search

    Attributes:
        api_key: The API key for the search engine.
        api_type: The type of search engine to use, defaults to SERPAPI_GOOGLE.
        cse_id: The Custom Search Engine ID, defaults to an empty string.
    """

    api_key: str
    api_type: SearchEngineType = SearchEngineType.SERPAPI_GOOGLE
    cse_id: str = ""  # for google
