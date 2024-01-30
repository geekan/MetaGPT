#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 19:07
# @Author  : alexanderwu
# @File    : mermaid_config.py

from typing import Literal

from metagpt.utils.yaml_model import YamlModel


class MermaidConfig(YamlModel):
    """Config for Mermaid.

    Attributes:
        engine: Engine to be used. Options are 'nodejs', 'ink', 'playwright', 'pyppeteer'.
        path: Path for the configuration.
        puppeteer_config: Configuration for Puppeteer.
    """

    engine: Literal["nodejs", "ink", "playwright", "pyppeteer"] = "nodejs"
    path: str = ""
    puppeteer_config: str = ""  # Only for nodejs engine
