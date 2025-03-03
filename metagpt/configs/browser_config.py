#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 19:06
@Author  : alexanderwu
@File    : browser_config.py
"""
from enum import Enum
from typing import Literal

from metagpt.utils.yaml_model import YamlModel


class WebBrowserEngineType(Enum):
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    CUSTOM = "custom"

    @classmethod
    def __missing__(cls, key):
        """Default type conversion"""
        return cls.CUSTOM


class BrowserConfig(YamlModel):
    """Config for Browser"""

    engine: WebBrowserEngineType = WebBrowserEngineType.PLAYWRIGHT
    browser_type: Literal["chromium", "firefox", "webkit", "chrome", "firefox", "edge", "ie"] = "chromium"
    """If the engine is Playwright, the value should be one of "chromium", "firefox", or "webkit". If it is Selenium, the value
    should be either "chrome", "firefox", "edge", or "ie"."""
