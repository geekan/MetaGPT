# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 19:46 PM
# @Author  : didi
# @Desc    : action nodes for operator

from pydantic import BaseModel, Field


class GenerateOp(BaseModel):
    response: str = Field(default="", description="Your solution for this problem")


class CodeGenerateOp(BaseModel):
    code: str = Field(default="", description="Your complete code solution for this problem")


class ScEnsembleOp(BaseModel):
    solution_letter: str = Field(default="", description="The letter of most consistent solution.")

