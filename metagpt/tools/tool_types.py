from metagpt.prompts.tool_type import (
    DATA_PREPROCESS_PROMPT,
    FEATURE_ENGINEERING_PROMPT,
    MODEL_TRAIN_PROMPT,
    MODEL_EVALUATE_PROMPT,
)
from metagpt.tools.tool_schema import ToolTypeEnum, ToolType
from metagpt.tools.tool_registry import register_tool_type


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
class Other(ToolType):
    name: str = ToolTypeEnum.OTHER.value
    desc: str = "Any tools not in the defined categories"
    usage_prompt: str = ""
