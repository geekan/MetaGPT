from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.mbpp import mbpp_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Tuple

MBPP_PROMPT = """
{question}\nPlease reason step by step, and put your python function in the end. 
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="问题的Python函数实现")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, question: str, mode: str = None) -> Tuple[str, str]:
        prompt = MBPP_PROMPT.format(question=question)
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

    async def __call__(self, question: str) -> Tuple[str, str]:
        response = await self.cot_generate(question, mode="context_fill")
        return response["solution"]

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        graph = CoTSolveGraph(name="CoT", llm_config=llm_config, dataset="MBPP")
        file_path = "examples/ags/data/mbpp-new.jsonl"
        samples = 30
        path = "examples/ags/data/baselines/general/mbpp"
        score = await mbpp_evaluation(graph, file_path, samples, path)
        return score

    import asyncio 
    asyncio.run(main())