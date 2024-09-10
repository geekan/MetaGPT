from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.math import math_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any

MATH_PROMPT_GPT = """
{question}\nPlease reason step by step, and put your final answer in the end. Wrap content using xml tags.
"""

MATH_PROMPT_DS = """
{question}\nPlease reason step by step, and put your final answer within \\boxed{{}}.
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="solution for the problem")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, mode: str = None):
        prompt = MATH_PROMPT_GPT.format(question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

class CoTSolveGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = CoTGenerate(self.llm)

    async def __call__(self, problem):
        solution = await self.cot_generate(problem, mode="context_fill")
        return solution, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        # llm_config = ModelsConfig.default().get("deepseek-coder")
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        graph = CoTSolveGraph(name="CoT", llm_config=llm_config, dataset="Gsm8K")
        file_path = "examples/ags/data/math.jsonl"
        samples = 100
        # samples = 100
        path = "examples/ags/data/baselines/general/math"
        score = await math_evaluation(graph, file_path, samples, path)
        return score

    import asyncio
    asyncio.run(main())


# self consistency operator; universal self consistency; 

# IO指的没有任何Trick，看LLM自身的一个效果。使用 model 发布者在对应的 dataset 使用的 prompt。

# deepseek-chat; gpt-4o-mini; gpt-35-turbo-1106



GENERATE_PROMPT = """
Generate Solution for the following problem: {problem_description}
"""

# med ensemble 