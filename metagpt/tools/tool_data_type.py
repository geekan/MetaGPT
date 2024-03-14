from pydantic import BaseModel


class ToolSchema(BaseModel):
    description: str


class Tool(BaseModel):
    name: str
    path: str
    schemas: dict = {}
    code: str = ""
    tags: list[str] = []
