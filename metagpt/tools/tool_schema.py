from enum import Enum

from pydantic import BaseModel


class ToolTypeEnum(Enum):
    DATA_PREPROCESS = "data_preprocess"
    FEATURE_ENGINEERING = "feature_engineering"
    MODEL_TRAIN = "model_train"
    MODEL_EVALUATE = "model_evaluate"
    OTHER = "other"

    def __missing__(self, key):
        return self.OTHER


class ToolType(BaseModel):
    name: str
    desc: str
    usage_prompt: str = ""


class ToolSchema(BaseModel):
    name: str


class Tool(BaseModel):
    name: str
    path: str
    schema: dict = {}
    code: str = ""
