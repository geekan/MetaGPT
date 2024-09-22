from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.gsm8k import gsm8k_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any

GSM8K_PROMPT_IO = """
{question}\nGenerate an answer to this question. At the end, provide the final answer in the format "Answer is <number>", where <number> is a single number.
"""


class GenerateOp(BaseModel):
    solution: str = Field(default="", description="solution for the problem")

class Generate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, mode: str = None):
        prompt = GSM8K_PROMPT_IO.format(question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

class GenerateSolveGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.generate = Generate(self.llm)

    async def __call__(self, problem):
        solution = await self.generate(problem, mode="context_fill")
        return solution, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        # llm_config = ModelsConfig.default().get("deepseek-coder")
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        graph = GenerateSolveGraph(name="Generate", llm_config=llm_config, dataset="Gsm8K")
        file_path = "examples/ags/data/gsm8k.jsonl"
        samples = 1219
        path = "examples/ags/data/baselines/general"
        score, cost = await gsm8k_evaluation(graph, file_path, samples, path, test=True)
        return score, cost

    import asyncio
    asyncio.run(main())


# medprompt operator; universal self consistency; 

# IO指的没有任何Trick，看LLM自身的一个效果。使用 model 发布者在对应的 dataset 使用的 prompt。

# deepseek-chat; gpt-4o-mini; gpt-35-turbo-1106

# med ensemble 