#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 19:06
@Author  : alexanderwu
@File    : search_config.py
"""
from typing import Callable, Optional

from metagpt.tools import SearchEngineType
from metagpt.utils.yaml_model import YamlModel


class SearchConfig(YamlModel):
    """Config for Search"""

    api_type: SearchEngineType = SearchEngineType.DUCK_DUCK_GO
    api_key: str = ""
    cse_id: str = ""  # for google
    search_func: Optional[Callable] = None
