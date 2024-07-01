# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 22:07 PM
# @Author  : didi
# @Desc    : graph & an instance - humanevalgraph

from metagpt.llm import LLM 

from examples.ags.w_action_node.operator import Generate, GenerateCode, Review, Revise, Ensemble, ScEnsemble

class Graph:
    def __init__(self, name:str, llm:LLM) -> None:
        self.name = name
        # TODO 是否需要对每一个算子使用不同的Graph？
        self.model = llm 

    def __call__():
        NotImplementedError("Subclasses must implement __call__ method")


class HumanEvalGraph(Graph):
    def __init__(self, name:str, llm: LLM, criteria:str) -> None:
        super().__init__(name, llm)
        self.criteria = criteria # TODO 自动构建图时，图的初始参数与图所使用的算子要求的外部参数相关
        self.generate_code = GenerateCode(llm=llm)
        self.review = Review(llm=llm, criteria=criteria)
        self.revise = Revise(llm=llm)
        self.ensemble = Ensemble(llm=llm)
        self.scensemble = ScEnsemble(llm=llm)
    
    # async def __call__(self, problem:str, ensemble_count:int = 2):
    #     solution_list = []
    #     for _ in range(ensemble_count):
    #         solution = await self.single_solve(problem, 3)
    #         solution_list.append(solution)
    #     solution = await self.ensemble(solution_list, problem)
    #     return solution

    async def __call__(self, problem:str):
        solution_list = []
        for _ in range(3):
            solution = await self.generate_code(problem)
            solution = solution.get('code_solution')
            solution_list.append(solution)
        solution = await self.ensemble(solution_list, problem)
        return solution
    
    # async def __call__(self, problem:str):
    #     solution_list = []
    #     for _ in range(3):
    #         solution = await self.generate_code(problem)
    #         solution = solution.get('code_solution')
    #         solution_list.append(solution)
    #     solution = await self.scensemble(solution_list, problem)
    #     return solution
    
    async def single_solve(self, problem:str, max_loop:int):
        solution = await self.generate_code(problem)
        solution = solution.get('code_solution')
        for _ in range(max_loop):
            review_feedback = await self.review(problem, solution)
            if review_feedback['review_result']:
                break
            solution = await self.revise(problem, solution, review_feedback['feedback'])
            solution = solution.get('revised_solution')
        return solution