# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 19:46 PM
# @Author  : didi
# @Desc    : action nodes for operator

from pydantic import BaseModel, Field

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="Your Solution for this problem")

class GenerateCodeOp(BaseModel):
    code_solution: str = Field(default="", description="Your Code Solution for this problem")

class GenerateCodeBlockOp(BaseModel):
    code_solution: str = Field(default="", description="Your Code Solution for this problem")

class ReviewOp(BaseModel):
    review_result: bool = Field(default=False, description="The Review Result (Bool). If you think this solution looks good for you, return 'true'; If not, return 'false'")
    feedback: str = Field(default="", description="Your FeedBack for this problem based on the criteria. If the review result is true, you can put it 'nothing here'.")

class ReviseOp(BaseModel):
    revised_solution: str = Field(default="", description="Based on the feedback, revised solution for this problem")

class EnsembleOp(BaseModel):
    final_solution: str = Field(default="", description="Final ensemble solution for this problem")

class MdEnsembleOp(BaseModel):
    thought: str = Field(default="",
                          description="Analyze the solutions and think what's the best step by step.")
    solution_letter: str = Field(default="",
                                 description="""
        Based on the problem and solution candidates, carefully analyze which is the best answer. Focus solely on the correctness of the solution in addressing the problem.
        Provide your final decision by writing the chosen solution number. (eg.A) """)