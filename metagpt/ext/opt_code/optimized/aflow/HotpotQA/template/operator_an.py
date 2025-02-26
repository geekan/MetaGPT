# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 19:46 PM
# @Author  : didi
# @Desc    : action nodes for operator

from pydantic import BaseModel, Field


class GenerateOp(BaseModel):
    response: str = Field(default="", description="Your response to the question.")
# class GenerateOp(BaseModel):
#     response: str = Field(default="", description="Your solution for this problem")


class ScEnsembleOp(BaseModel):
    thought: str = Field(default="", description="The thought of the most consistent solution.")
    solution_letter: str = Field(default="", description="The letter of most consistent solution.")

class AnswerGenerateOp(BaseModel):
    response: str = Field(default="", description="Your response to the question.")
    answer: str = Field(default="", description="The final answer to the question.")