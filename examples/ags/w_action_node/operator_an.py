# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 19:46 PM
# @Author  : didi
# @Desc    : action nodes for operator

from pydantic import BaseModel, Field

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="Your Solution for this problem")

class GenerateCodeOp(BaseModel):
    code_solution: str = Field(default="", description="Complete and correct code here.")

class GenerateCodeBlockOp(BaseModel):
    code_solution: str = Field(default="", description="Your complete code solution for this problem")

class ReviewOp(BaseModel):
    review_result: bool = Field(default=False, description="The Review Result (Bool). If you think this solution looks good for you, return 'true'; If not, return 'false'")
    feedback: str = Field(default="", description="Your FeedBack for this problem based on the criteria. If the review result is true, you can put it 'nothing here'.")

class ReviseOp(BaseModel):
    revised_solution: str = Field(default="", description="Based on the feedback, revised solution for this problem")

class FuEnsembleOp(BaseModel):
    thought: str = Field(default="", description="Analyze the solutions and think how to combine the advantages of various solutions to form the best possible solution.")
    final_solution: str = Field(default="", description="Output the final solution after analysis and integration")

class MdEnsembleOp(BaseModel):
    thought: str = Field(
        default="""Example thought process:
                1. Examined the 'compare_one' function.
                2. The function correctly handles both numeric and string inputs by converting strings to floats.
                3. It properly compares two values and returns the larger one.
                4. The function returns None if the values are equal, which might be useful in some contexts but could be improved by returning either value.
                5. The use of 'isinstance' for type checking is a good practice.
                6. The function handles decimal separators well by replacing ',' with '.'.
                Overall, this solution effectively solves the problem of comparing two values, with good error handling and flexibility. It could be improved by specifying behavior for equal values, but it's a strong solution as is.""",
        description="Step-by-step analysis of the solutions to determine the best one."
    )
    solution_letter: str = Field(
        default="",
        description="The letter of the chosen best solution (only one letter)."
    )

