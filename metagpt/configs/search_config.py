#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 19:06
@Author  : alexanderwu
@File    : search_config.py
"""
from metagpt.tools import SearchEngineType
from metagpt.utils.yaml_model import YamlModel


class SearchConfig(YamlModel):
    """Config for Search"""

    api_key: str
    api_type: SearchEngineType = SearchEngineType.SERPAPI_GOOGLE
    cse_id: str = ""  # for google
