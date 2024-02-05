from pydantic import BaseModel


class ToolTypeDef(BaseModel):
    name: str
    desc: str = ""
    usage_prompt: str = ""


class ToolSchema(BaseModel):
    description: str


class Tool(BaseModel):
    name: str
    path: str
    schemas: dict = {}
    code: str = ""
