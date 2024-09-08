from examples.ags.scripts.operator import Operator
from examples.ags.scripts.optimized.Gsm8K.operators.Rephrase.round_1.prompt import *
from examples.ags.scripts.optimized.Gsm8K.operators.template.operator_an import *
from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM


class Rephrase(Operator):
    """
    Paper: Code Generation with AlphaCodium: From Prompt Engineering to Flow Engineering
    Link: https://arxiv.org/abs/2404.14963
    Paper: Achieving >97% on GSM8K: Deeply Understanding the Problems Makes LLMs Better Solvers for Math Word Problems
    Link: https://arxiv.org/abs/2404.14963
    """

    def __init__(self, llm: LLM, name: str = "Rephrase"):
        super().__init__(name, llm)

    async def __call__(self, problem: str) -> str:
        prompt = REPHRASE_PROMPT.format(problem=problem)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm, mode="single_fill")
        response = node.instruct_content.model_dump()
        return response  # {"rephrased_problem": "xxx"}
