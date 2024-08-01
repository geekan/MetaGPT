from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM

from examples.ags.w_action_node.operator_an import GenerateOp, RephraseOp
from examples.ags.w_action_node.math_prompt import GENERATE_PROMPT, REPHRASE_ON_PROBLEM_PROMPT, ANSWER_FORMAT_PROMPT


class Operator:
    def __init__(self, name, llm: LLM):
        self.name = name
        self.llm = llm

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class Generate(Operator):
    def __init__(self, name: str = "Generator", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description):
        prompt = GENERATE_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

class Rephrase(Operator):
    """
    1. AlphaCodium
    2. https://arxiv.org/abs/2404.14963
    """

    def __init__(self, name: str = "Rephraser", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description: str) -> str:
        prompt = REPHRASE_ON_PROBLEM_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response["rephrased_problem"]

class Format(Operator):
    def __init__(self, name: str = "Formatter", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description):
        try:
            prompt = ANSWER_FORMAT_PROMPT.format(problem_description=problem_description)
            node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm)
            response = node.instruct_content.model_dump()
            return response
        except Exception as e:
            print(f"Error in Format: {e}")  # 错误信息
            raise



