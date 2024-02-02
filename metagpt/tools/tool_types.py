from enum import Enum

from metagpt.prompts.tool_types import (
    DATA_PREPROCESS_PROMPT,
    FEATURE_ENGINEERING_PROMPT,
    IMAGE2WEBPAGE_PROMPT,
    MODEL_EVALUATE_PROMPT,
    MODEL_TRAIN_PROMPT,
)
from metagpt.tools.tool_data_type import ToolType

Eda = ToolType(name="eda", desc="For performing exploratory data analysis")

DataPreprocess = ToolType(
    name="data_preprocess",
    desc="Only for changing value inplace.",
    usage_prompt=DATA_PREPROCESS_PROMPT,
)


FeatureEngineering = ToolType(
    name="feature_engineering",
    desc="Only for creating new columns for input data.",
    usage_prompt=FEATURE_ENGINEERING_PROMPT,
)


ModelTrain = ToolType(
    name="model_train",
    desc="Only for training model.",
    usage_prompt=MODEL_TRAIN_PROMPT,
)


ModelEvaluate = ToolType(
    name="model_evaluate",
    desc="Only for evaluating model.",
    usage_prompt=MODEL_EVALUATE_PROMPT,
)


StableDiffusion = ToolType(
    name="stable_diffusion",
    desc="Related to text2image, image2image using stable diffusion model.",
)


Image2Webpage = ToolType(
    name="image2webpage",
    desc="For converting image into webpage code.",
    usage_prompt=IMAGE2WEBPAGE_PROMPT,
)


WebScraping = ToolType(
    name="web_scraping",
    desc="For scraping data from web pages.",
)


Other = ToolType(name="other", desc="Any tools not in the defined categories")


class ToolTypes(Enum):
    EDA = Eda
    DATA_PREPROCESS = DataPreprocess
    FEATURE_ENGINEERING = FeatureEngineering
    MODEL_TRAIN = ModelTrain
    MODEL_EVALUATE = ModelEvaluate
    STABLE_DIFFUSION = StableDiffusion
    IMAGE2WEBPAGE = Image2Webpage
    WEBSCRAPING = WebScraping
    OTHER = Other

    def __missing__(self, key):
        return self.OTHER

    @property
    def type_name(self):
        return self.value.name
