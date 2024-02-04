from enum import Enum

from metagpt.prompts.tool_types import (
    DATA_PREPROCESS_PROMPT,
    FEATURE_ENGINEERING_PROMPT,
    IMAGE2WEBPAGE_PROMPT,
    MODEL_EVALUATE_PROMPT,
    MODEL_TRAIN_PROMPT,
)
from metagpt.tools.tool_data_type import ToolType


class ToolTypes(Enum):
    EDA = ToolType(name="eda", desc="For performing exploratory data analysis")
    DATA_PREPROCESS = ToolType(
        name="data_preprocess",
        desc="Only for changing value inplace.",
        usage_prompt=DATA_PREPROCESS_PROMPT,
    )
    FEATURE_ENGINEERING = ToolType(
        name="feature_engineering",
        desc="Only for creating new columns for input data.",
        usage_prompt=FEATURE_ENGINEERING_PROMPT,
    )
    MODEL_TRAIN = ToolType(
        name="model_train",
        desc="Only for training model.",
        usage_prompt=MODEL_TRAIN_PROMPT,
    )
    MODEL_EVALUATE = ToolType(
        name="model_evaluate",
        desc="Only for evaluating model.",
        usage_prompt=MODEL_EVALUATE_PROMPT,
    )
    STABLE_DIFFUSION = ToolType(
        name="stable_diffusion",
        desc="Related to text2image, image2image using stable diffusion model.",
    )
    IMAGE2WEBPAGE = ToolType(
        name="image2webpage",
        desc="For converting image into webpage code.",
        usage_prompt=IMAGE2WEBPAGE_PROMPT,
    )
    WEBSCRAPING = ToolType(
        name="web_scraping",
        desc="For scraping data from web pages.",
    )
    OTHER = ToolType(name="other", desc="Any tools not in the defined categories")

    def __missing__(self, key):
        return self.OTHER

    @property
    def type_name(self):
        return self.value.name
