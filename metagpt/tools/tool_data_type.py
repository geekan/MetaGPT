from pydantic import BaseModel


class ToolType(BaseModel):
    name: str
    desc: str = ""
    usage_prompt: str = ""


class ToolSchema(BaseModel):
    name: str


class Tool(BaseModel):
    name: str
    path: str
    schemas: dict = {}
    code: str = ""
