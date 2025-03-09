#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 19:06
@Author  : alexanderwu
@File    : search_config.py
"""
from enum import Enum
from typing import Callable, Optional

from pydantic import ConfigDict, Field

from metagpt.utils.yaml_model import YamlModel


class SearchEngineType(Enum):
    SERPAPI_GOOGLE = "serpapi"
    SERPER_GOOGLE = "serper"
    DIRECT_GOOGLE = "google"
    DUCK_DUCK_GO = "ddg"
    CUSTOM_ENGINE = "custom"
    BING = "bing"


class SearchConfig(YamlModel):
    """Config for Search"""

    model_config = ConfigDict(extra="allow")

    api_type: SearchEngineType = SearchEngineType.DUCK_DUCK_GO
    api_key: str = ""
    cse_id: str = ""  # for google
    search_func: Optional[Callable] = None
    params: dict = Field(
        default_factory=lambda: {
            "engine": "google",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
        }
    )
