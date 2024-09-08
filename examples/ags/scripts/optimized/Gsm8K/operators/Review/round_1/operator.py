from examples.ags.scripts.operator import Operator
from examples.ags.scripts.optimized.Gsm8K.operators.Review.round_1.prompt import *
from examples.ags.scripts.optimized.Gsm8K.operators.template.operator_an import *
from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM


class Review(Operator):
    def __init__(self, llm: LLM, criteria: str = "accuracy", name: str = "Review"):
        self.criteria = criteria
        super().__init__(name, llm)

    async def __call__(self, problem, solution):
        prompt = REVIEW_PROMPT.format(problem=problem, solution=solution, criteria=self.criteria)
        node = await ActionNode.from_pydantic(ReviewOp).fill(context=prompt, llm=self.llm, mode="context_fill")
        response = node.instruct_content.model_dump()
        return response  # {"review_result": True, "feedback": "xxx"}
