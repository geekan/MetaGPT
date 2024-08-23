# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 19:46 PM
# @Author  : didi
# @Desc    : action nodes for operator

from pydantic import BaseModel, Field


class GenerateOp(BaseModel):
    solution: str = Field(default="", description="Your solution for this problem")


class GenerateCodeBlockOp(BaseModel):
    code_solution: str = Field(default="", description="Your complete code solution for this problem")


class GenerateCodeSolution(BaseModel):
    content: str = Field(default="", description="A description of the solution")
    thought: str = Field(
        default="",
        description="Shortly explain why this solution correctly solves the problem. Be specific and detailed regarding the problem rules and goals.",
    )


class FormatOp(BaseModel):
    solution: str = Field(default="", description="Your formatted answer for this problem")


class ReviewOp(BaseModel):
    review_result: bool = Field(
        default=False,
        description="The Review Result (Bool). If you think this solution looks good for you, return 'true'; If not, return 'false'",
    )
    feedback: str = Field(
        default="",
        description="Your FeedBack for this problem based on the criteria. If the review result is true, you can put it 'nothing here'.",
    )


class ReviseOp(BaseModel):
    revised_solution: str = Field(default="", description="Based on the feedback, revised solution for this problem")


class FuEnsembleOp(BaseModel):
    thought: str = Field(
        default="",
        description="Analyze the solutions and think how to combine the advantages of various solutions to form the best possible solution.",
    )
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
        description="Step-by-step analysis of the solutions to determine the best one.",
    )
    solution_letter: str = Field(default="", description="The letter of the chosen best solution (only one letter).")


class TestCaseExtractOp(BaseModel):
    test_cases: list = Field(
        default=[
            "assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True",
            "assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False",
            "",
        ],
        description="Extracted test cases from the problem description",
    )


class RephraseOp(BaseModel):
    rephrased_problem: str = Field(default="", description="Rephrased problem description for this problem")


class ReflectionTestOp(BaseModel):
    reflection: str = Field(
        default="", description="Step-by-step reflection on code execution errors or test case failures"
    )
    refined_solution: str = Field(
        default="", description="Corrective solution for code execution errors or test case failures"
    )


class Optimize(BaseModel):
    graph: str = Field(default="", description="graph")
