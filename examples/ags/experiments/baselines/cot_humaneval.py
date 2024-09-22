from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.humaneval import humaneval_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field

HUMANEVAL_PROMPT_GPT = """
{question}\nPlease provide a step-by-step explanation in text, followed by your Python function without any additional text or test cases. 
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="Python Solution For This Question.")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, function_name, mode: str = None):
        prompt = HUMANEVAL_PROMPT_GPT.format(question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm, "function_name": function_name}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

class CoTSolveGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = CoTGenerate(self.llm)

    async def __call__(self, problem, function_name):
        solution = await self.cot_generate(problem, function_name, mode="code_fill")
        return solution["solution"], self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        # llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        # llm_config = ModelsConfig.default().get("deepseek-chat")
        llm_config = ModelsConfig.default().get("gpt-4o")
        graph = CoTSolveGraph(name="CoT", llm_config=llm_config, dataset="HumanEval")
        file_path = "examples/ags/data/baseline_data/human-eval.jsonl"
        samples = 33 # 33/131  
        path = "examples/ags/data/baselines/general/humaneval"
        score = await humaneval_evaluation(graph, file_path, samples, path,test=True)
        return score

    import asyncio
    asyncio.run(main())
