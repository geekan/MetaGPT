from examples.ags.scripts.operator import Operator
from examples.ags.scripts.optimized.Gsm8K.operators.Revise.round_1.prompt import *
from examples.ags.scripts.optimized.Gsm8K.operators.template.operator_an import *
from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM


class Revise(Operator):
    def __init__(self, llm: LLM, name: str = "Revise"):
        super().__init__(name, llm)

    async def __call__(self, problem, solution, feedback):
        prompt = REVISE_PROMPT.format(problem=problem, solution=solution, feedback=feedback)
        node = await ActionNode.from_pydantic(ReviseOp).fill(context=prompt, llm=self.llm, mode="single_fill")
        response = node.instruct_content.model_dump()
        return response  # {"solution": "xxx"}
