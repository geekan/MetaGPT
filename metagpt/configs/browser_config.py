#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 19:06
@Author  : alexanderwu
@File    : browser_config.py
"""
from typing import Literal

from metagpt.tools import WebBrowserEngineType
from metagpt.utils.yaml_model import YamlModel


class BrowserConfig(YamlModel):
    """Config for Browser"""

    engine: WebBrowserEngineType = WebBrowserEngineType.PLAYWRIGHT
    browser: Literal["chrome", "firefox", "edge", "ie"] = "chrome"
    driver: Literal["chromium", "firefox", "webkit"] = "chromium"
    path: str = ""
