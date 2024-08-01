from metagpt.llm import LLM
from typing import List
from examples.ags.w_action_node.math_operator import Generate, Rephrase, Format


class Graph:
    def __init__(self, name: str, llm: LLM) -> None:
        self.name = name
        self.model = llm

    def __call__():
        NotImplementedError("Subclasses must implement __call__ method")

    def optimize(dataset: List):
        pass


class Gsm8kGraph(Graph):
    def __init__(self, name: str, llm: LLM) -> None:
        super().__init__(name, llm)
        self.generate = Generate(llm=llm)
        self.rephrase = Rephrase(llm=llm)
        self.format = Format(llm=llm)

    async def __call__(self, problem: str):
        formatted_problem = await self.rephrase(problem)
        solution = await self.generate(formatted_problem)  # 确保等待 generate 方法完成
        solution0 = solution['solution']
        formatted_solution = await self.format(solution0)  # 确保等待 generate 方法完成
        return formatted_solution
