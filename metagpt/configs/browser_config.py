#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 19:06
# @Author  : alexanderwu
# @File    : browser_config.py

from typing import Literal

from metagpt.tools import WebBrowserEngineType
from metagpt.utils.yaml_model import YamlModel


class BrowserConfig(YamlModel):
    """Config for Browser

    Attributes:
        engine: The engine used by the browser.
        browser: The type of browser to use. Options are 'chrome', 'firefox', 'edge', 'ie'.
        driver: The driver for the browser. Options are 'chromium', 'firefox', 'webkit'.
        path: The path to the browser executable.
    """

    engine: WebBrowserEngineType = WebBrowserEngineType.PLAYWRIGHT
    browser: Literal["chrome", "firefox", "edge", "ie"] = "chrome"
    driver: Literal["chromium", "firefox", "webkit"] = "chromium"
    path: str = ""
