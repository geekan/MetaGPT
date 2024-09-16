from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.gsm8k import gsm8k_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any

GSM8K_PROMPT_GPT = """
{question}\nPlease reason step by step. At the end, provide the final answer in the format "Answer is <number>", where <number> is a single number, without any additional information or explanation.
"""

GSM8K_PROMPT_DS = """
{question}\nPlease reason step by step, and put your final answer within \\boxed{{}}.
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="solution for the problem")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, mode: str = None):
        prompt = GSM8K_PROMPT_GPT.format(question=problem)
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
        return solution, self.llm.cost_manager.total_cost # {"solution": solution}

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("deepseek-coder")
        # llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        # llm_config = ModelsConfig.default().get("gpt-4o")
        graph = CoTSolveGraph(name="CoT", llm_config=llm_config, dataset="Gsm8K")
        file_path = "examples/ags/data/gsm8k.jsonl"
        samples = 264 #264 # 1055 #314  
        # samples = 100
        path = "examples/ags/data/baselines/general/gsm8k/"
        score, cost = await gsm8k_evaluation(graph, file_path, samples, path, test=False)
        return score, cost 

    import asyncio
    asyncio.run(main())
    

# self consistency; medprompt 已有的Operator来实现这两个方法