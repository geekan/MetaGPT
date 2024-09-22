from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.mbpp import mbpp_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field

MBPP_PROMPT_IO = """
{question}\nGenerate an answer to this question, ensure the output code is self-contained, meaning it should have the correct function name and return statement, but without any additional test cases.
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="Python Solution For This Question.")

class Generate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, function_name, mode: str = None):
        prompt = MBPP_PROMPT_IO.format(question=problem)
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
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("deepseek-chat")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo")
        graph = IOSolveGraph(name="Io", llm_config=llm_config, dataset="MBPP")
        # result = await graph("Write a function to round every number of a given list of numbers and print the total sum multiplied by the length of the list.\n\ndef round_and_sum(list1):", "round_and_sum")
        # print(result)

        file_path = "examples/ags/data/mbpp-new-new.jsonl"
        samples = 86 # 86/341
        path = "examples/ags/data/baselines/general/mbpp"
        score = await mbpp_evaluation(graph, file_path, samples, path, test=True)
        return score

    import asyncio
    asyncio.run(main())
