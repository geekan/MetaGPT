# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 19:46 PM
# @Author  : didi
# @Desc    : action nodes for operator

from pydantic import BaseModel, Field
from metagpt.actions.action_node import ActionNode

SOLUTION = ActionNode(
    key="solution",
    expected_type=str,
    instruction="Your Solution for this problem",
    example=""
)

CODE_SOLUTION = ActionNode(
    key="code_solution",
    expected_type=str,
    instruction="Your Code Solution for this problem",
    example=""    
)

REVIEW_RESULT = ActionNode(
    key="review_result",
    expected_type=bool,
    instruction="The Review Result (Bool). If you think this solution looks good for you, return 'true'; If not, return 'false'",
    example=""    
)

FEEDBACK = ActionNode(
    key="feedback",
    expected_type=str,
    instruction="Your FeedBack for this problem based on the criteria. If the review result is true, you can put it 'nothing here'.",
    example=""    
)

GENERATE_NODE =  ActionNode.from_children("Generate", [SOLUTION])
GENERATE_CODE_NODE = ActionNode.from_children("GenerateCode", [CODE_SOLUTION])
REVIEW_NODE = ActionNode.from_children("Review", [REVIEW_RESULT, FEEDBACK])
REVISE_NODE = ActionNode.from_children("Revise", [SOLUTION])
ENSEMBLE_NODE = ActionNode.from_children("Ensemble", [SOLUTION])

class Generate(BaseModel):
    solution: str = Field(default="", description="Your Solution for this problem")

class GenerateCode(BaseModel):
    code_solution: str = Field(default="", description="Your Code Solution for this problem")

class Review(BaseModel):
    review_result: bool = Field(default=False, description="The Review Result (Bool). If you think this solution looks good for you, return 'true'; If not, return 'false'")
    feedback: str = Field(default="", description="Your FeedBack for this problem based on the criteria. If the review result is true, you can put it 'nothing here'.")

class Revise(BaseModel):
    revised_solution: str = Field(default="", description="Revised solution for this problem")

class Ensemble(BaseModel):
    final_solution: str = Field(default="", description="Final ensemble solution for this problem")




# 接下来我将给予你两段代码，请你按照我的要求对其进行改写
# 第一段代码是一个利用子ActionNode通过From_children方法实现的多个Node聚合
# 第二段代码是一个利用Pydantic与From_pydantic方法实现的Node
# 现在，我希望你能够通过From Pydantic方法，通过第二段代码的风格，完成我第一段代码中的GENERATE -> ENSEMBLE 五个Node的实现，每一个实现都应该像是第二段代码中的一个Class一样