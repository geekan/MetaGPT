from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.humaneval import humaneval_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field

HUMANEVAL_PROMPT_IO = """
{question}\nGenerate an answer to this question, without any additional test cases. 
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="Python Solution For This Question.")

class Generate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, function_name, mode: str = None):
        prompt = HUMANEVAL_PROMPT_IO.format(question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm, "function_name": function_name}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

class IOSolveGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = Generate(self.llm)

    async def __call__(self, problem, function_name):
        solution = await self.cot_generate(problem, function_name, mode="code_fill")
        return solution["solution"], self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        # llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-4o")
        # llm_config = ModelsConfig.default().get("deepseek-chat")
        llm_config = ModelsConfig.default().get("claude-3-5-sonnet-20240620")
        graph = IOSolveGraph(name="Io", llm_config=llm_config, dataset="HumanEval")
        file_path = "examples/ags/data/baseline_data/human-eval.jsonl"
        samples = 33 # 33/131  
        path = "examples/ags/data/baselines/general/humaneval"
        score = await humaneval_evaluation(graph, file_path, samples, path,test=True)
        return score

    import asyncio
    asyncio.run(main())
