#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:35
@Author  : alexanderwu
@File    : __init__.py
"""

from enum import Enum

from pydantic import BaseModel

from metagpt.const import TOOL_LIBS_PATH
from metagpt.prompts.tool_type import (
    DATA_PREPROCESS_PROMPT,
    FEATURE_ENGINEERING_PROMPT,
    MODEL_TRAIN_PROMPT,
    MODEL_EVALUATE_PROMPT,
)


class SearchEngineType(Enum):
    SERPAPI_GOOGLE = "serpapi"
    SERPER_GOOGLE = "serper"
    DIRECT_GOOGLE = "google"
    DUCK_DUCK_GO = "ddg"
    CUSTOM_ENGINE = "custom"


class WebBrowserEngineType(Enum):
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    CUSTOM = "custom"

    @classmethod
    def __missing__(cls, key):
        """Default type conversion"""
        return cls.CUSTOM


class ToolType(BaseModel):
    name: str
    module: str = ""
    desc: str
    usage_prompt: str = ""


TOOL_TYPE_MAPPINGS = {
    "data_preprocess": ToolType(
        name="data_preprocess",
        module=str(TOOL_LIBS_PATH / "data_preprocess"),
        desc="Only for changing value inplace.",
        usage_prompt=DATA_PREPROCESS_PROMPT,
    ),
    "feature_engineering": ToolType(
        name="feature_engineering",
        module=str(TOOL_LIBS_PATH / "feature_engineering"),
        desc="Only for creating new columns for input data.",
        usage_prompt=FEATURE_ENGINEERING_PROMPT,
    ),
    "model_train": ToolType(
        name="model_train",
        module="",
        desc="Only for training model.",
        usage_prompt=MODEL_TRAIN_PROMPT,
    ),
    "model_evaluate": ToolType(
        name="model_evaluate",
        module="",
        desc="Only for evaluating model.",
        usage_prompt=MODEL_EVALUATE_PROMPT,
    ),
    "stable_diffusion": ToolType(
        name="stable_diffusion",
        module="metagpt.tools.sd_engine",
        desc="Related to text2image, image2image using stable diffusion model.",
        usage_prompt="",
    ),
    "scrape_web": ToolType(
        name="scrape_web",
        module="metagpt.tools.scrape_web",
        desc="Scrape data from web page.",
        usage_prompt="",
    ),
    "other": ToolType(
        name="other",
        module="",
        desc="Any tasks that do not fit into the previous categories",
        usage_prompt="",
    ),
}
