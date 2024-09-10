from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.humaneval import humaneval_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field

HUMANEVAL_PROMPT_GPT = """
{question}\nPlease reason step by step, and put your python function in the end. 
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="问题的Python函数实现")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, mode: str = None):
        prompt = HUMANEVAL_PROMPT_GPT.format(question=problem)
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
        solution = await self.cot_generate(problem, mode="code_fill")
        return solution["solution"]

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        graph = CoTSolveGraph(name="CoT", llm_config=llm_config, dataset="HumanEval")
        file_path = "examples/ags/data/human-eval-new.jsonl"
        samples = 1 # 33/131  
        path = "examples/ags/data/baselines/general"
        score = await humaneval_evaluation(graph, file_path, samples, path)
        return score

    import asyncio
    asyncio.run(main())
