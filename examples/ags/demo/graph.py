# -*- coding: utf-8 -*-
# @Date    : 6/26/2024 17:07 PM
# @Author  : didi
# @Desc    : graph demo of ags

from examples.ags.demo.operator import Generate, GenerateCode, Review, Revise, Ensemble, LLM

class Graph:
    def __init__(self, name:str, llm:str) -> None:
        self.name = name
        self.model = llm # TODO 抽象一个逻辑，用不同的model适配不同的算子

    def __call__():
        NotImplementedError("Subclasses must implement __call__ method")


class HumanEvalGraph(Graph):
    def __init__(self, name:str, llm: str, criteria:str) -> None:
        super().__init__(name, llm)
        self.criteria = criteria # TODO 有位置参数的生成逻辑是基于算子的要求
        self.generate_code = GenerateCode(llm=LLM(model=llm))
        self.review = Review(llm=LLM(model=llm), criteria=criteria)
        self.revise = Revise(llm=LLM(model=llm))
        self.ensemble = Ensemble(llm=LLM(model=llm))

    def __call__(self, problem):
        # TODO 我先来实现一版不带Ensemble的版本
        solution = self.generate_code(problem)
        # review & revise loop
        for _ in range(3):
            review_feedback = self.review(problem, solution)
            if review_feedback['result']:
                break
            solution = self.revise(solution, review_feedback['feedback'])
        return solution
    

