from enum import Enum

from metagpt.prompts.tool_types import (
    DATA_PREPROCESS_PROMPT,
    EDA_PROMPT,
    FEATURE_ENGINEERING_PROMPT,
    IMAGE2WEBPAGE_PROMPT,
    MODEL_EVALUATE_PROMPT,
    MODEL_TRAIN_PROMPT,
)
from metagpt.tools.tool_data_type import ToolTypeDef


class ToolType(Enum):
    EDA = ToolTypeDef(
        name="eda",
        desc="For performing exploratory data analysis",
        usage_prompt=EDA_PROMPT,
    )
    DATA_PREPROCESS = ToolTypeDef(
        name="data_preprocess",
        desc="Only for changing value inplace.",
        usage_prompt=DATA_PREPROCESS_PROMPT,
    )
    EMAIL_LOGIN = ToolTypeDef(
        name="email_login",
        desc="For logging to an email.",
    )
    FEATURE_ENGINEERING = ToolTypeDef(
        name="feature_engineering",
        desc="Only for creating new columns for input data.",
        usage_prompt=FEATURE_ENGINEERING_PROMPT,
    )
    MODEL_TRAIN = ToolTypeDef(
        name="model_train",
        desc="Only for training model.",
        usage_prompt=MODEL_TRAIN_PROMPT,
    )
    MODEL_EVALUATE = ToolTypeDef(
        name="model_evaluate",
        desc="Only for evaluating model.",
        usage_prompt=MODEL_EVALUATE_PROMPT,
    )
    STABLE_DIFFUSION = ToolTypeDef(
        name="stable_diffusion",
        desc="Related to text2image, image2image using stable diffusion model.",
    )
    IMAGE2WEBPAGE = ToolTypeDef(
        name="image2webpage",
        desc="For converting image into webpage code.",
        usage_prompt=IMAGE2WEBPAGE_PROMPT,
    )
    WEBSCRAPING = ToolTypeDef(
        name="web_scraping",
        desc="For scraping data from web pages.",
    )
    OTHER = ToolTypeDef(name="other", desc="Any tools not in the defined categories")

    def __missing__(self, key):
        return self.OTHER

    @property
    def type_name(self):
        return self.value.name
