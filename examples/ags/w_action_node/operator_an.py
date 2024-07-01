# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 19:46 PM
# @Author  : didi
# @Desc    : action nodes for operator

from pydantic import BaseModel, Field

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="Your Solution for this problem")

class GenerateCodeOp(BaseModel):
    code_solution: str = Field(default="", description="Your Code Solution for this problem")

class ReviewOp(BaseModel):
    review_result: bool = Field(default=False, description="The Review Result (Bool). If you think this solution looks good for you, return 'true'; If not, return 'false'")
    feedback: str = Field(default="", description="Your FeedBack for this problem based on the criteria. If the review result is true, you can put it 'nothing here'.")

class ReviseOp(BaseModel):
    revised_solution: str = Field(default="", description="Based on the feedback, revised solution for this problem")

class EnsembleOp(BaseModel):
    final_solution: str = Field(default="", description="Final ensemble solution for this problem")

class ScEnsembleOp(BaseModel):
    solution_number: int = Field(default="", description="Choose The Best Solution Between These, and outp[ut the solution number")