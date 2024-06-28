from typing import Literal

from pydantic import BaseModel, Field


class Point(BaseModel):
    id: int = Field(default=0, description="ID of the point.")
    text: str = Field(default="", description="Content of the point.")
    language: Literal["Python", "Java"] = Field(
        default="Python", description="The programming language that the point corresponds to."
    )
    file_path: str = Field(default="", description="The file that the points come from.")
    start_line: int = Field(default=0, description="The starting line number that the point refers to.")
    end_line: int = Field(default=0, description="The ending line number that the point refers to.")
    detail: str = Field(default="", description="File content from start_line to end_line.")
    yes_example: str = Field(default="", description="yes of point examples")
    no_example: str = Field(default="", description="no of point examples")

    def rag_key(self) -> str:
        return self.text
