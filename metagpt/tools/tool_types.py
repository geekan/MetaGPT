from metagpt.prompts.tool_types import (
    DATA_PREPROCESS_PROMPT,
    FEATURE_ENGINEERING_PROMPT,
    IMAGE2WEBPAGE_PROMPT,
    MODEL_EVALUATE_PROMPT,
    MODEL_TRAIN_PROMPT,
)
from metagpt.tools.tool_data_type import ToolType, ToolTypeEnum
from metagpt.tools.tool_registry import register_tool_type


@register_tool_type
class EDA(ToolType):
    name: str = ToolTypeEnum.EDA.value
    desc: str = "For performing exploratory data analysis"


@register_tool_type
class DataPreprocess(ToolType):
    name: str = ToolTypeEnum.DATA_PREPROCESS.value
    desc: str = "Only for changing value inplace."
    usage_prompt: str = DATA_PREPROCESS_PROMPT


@register_tool_type
class FeatureEngineer(ToolType):
    name: str = ToolTypeEnum.FEATURE_ENGINEERING.value
    desc: str = "Only for creating new columns for input data."
    usage_prompt: str = FEATURE_ENGINEERING_PROMPT


@register_tool_type
class ModelTrain(ToolType):
    name: str = ToolTypeEnum.MODEL_TRAIN.value
    desc: str = "Only for training model."
    usage_prompt: str = MODEL_TRAIN_PROMPT


@register_tool_type
class ModelEvaluate(ToolType):
    name: str = ToolTypeEnum.MODEL_EVALUATE.value
    desc: str = "Only for evaluating model."
    usage_prompt: str = MODEL_EVALUATE_PROMPT


@register_tool_type
class StableDiffusion(ToolType):
    name: str = ToolTypeEnum.STABLE_DIFFUSION.value
    desc: str = "Related to text2image, image2image using stable diffusion model."


@register_tool_type
class Image2Webpage(ToolType):
    name: str = ToolTypeEnum.IMAGE2WEBPAGE.value
    desc: str = "For converting image into webpage code."
    usage_prompt: str = IMAGE2WEBPAGE_PROMPT


@register_tool_type
class WebScraping(ToolType):
    name: str = ToolTypeEnum.WEBSCRAPING.value
    desc: str = "For scraping data from web pages."


@register_tool_type
class Other(ToolType):
    name: str = ToolTypeEnum.OTHER.value
    desc: str = "Any tools not in the defined categories"
