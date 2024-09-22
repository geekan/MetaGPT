from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.math import math_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any

GENERATE_IO_PROMPT = """
{question}\nPlease generate a solution for the problem. At the end, provide the final answer in the format "\\boxed{{<number>}}", where <number> is a math answer(an expression or number), without any additional information or explanation.
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="solution for the problem")

class IOGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, mode: str = None):
        prompt = GENERATE_IO_PROMPT.format(question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

class IOSolveGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = IOGenerate(self.llm)

    async def __call__(self, problem):
        solution = await self.cot_generate(problem, mode="context_fill")
        return solution, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        # llm_config = ModelsConfig.default().get("deepseek-coder")
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        graph = IOSolveGraph(name="CoT", llm_config=llm_config, dataset="Gsm8K")
        file_path = "examples/ags/data/math_test.jsonl" #486
        # samples = None
        samples = 0
        path = "examples/ags/data/baselines/general/math"
        score = await math_evaluation(graph, file_path, samples, path,test=True)
        return score

    import asyncio
    asyncio.run(main())