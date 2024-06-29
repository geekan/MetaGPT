# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 17:36 PM
# @Author  : didi
# @Desc    : operator demo of ags

from typing import List

from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM 

from examples.ags.w_action_node.operator_an import GenerateOp, GenerateCodeOp, ReviewOp, ReviseOp, EnsembleOp
from examples.ags.w_action_node.prompt import GENERATE_PROMPT, GENERATE_CODE_PROMPT, REVIEW_PROMPT, REVISE_PROMPT, ENSEMBLE_PROMPT

class Operator:
    def __init__(self, name, llm:LLM=None):
        self.name = name
        self.llm = llm

    def __call__(self, *args, **kwargs):
        raise NotImplementedError

class Generate(Operator):
    def __init__(self, name:str ="Generator", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description):
        prompt = GENERATE_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response
    
class GenerateCode(Operator):

    def __init__(self, name:str ="Coder", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description):
        prompt = GENERATE_CODE_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(GenerateCodeOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response
    
class Review(Operator):
    
    def __init__(self, criteria, name:str ="Reviewer", llm: LLM = LLM()):
        self.criteria = criteria
        super().__init__(name, llm)

    async def __call__(self, problem_description, solution):
        prompt = REVIEW_PROMPT.format(problem_description=problem_description, solution=solution, criteria=self.criteria)
        node = await ActionNode.from_pydantic(ReviewOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

class Revise(Operator):

    def __init__(self, name:str ="Reviser", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description, solution, feedback):
        prompt = REVISE_PROMPT.format(problem_description=problem_description, solution=solution, feedback=feedback)
        node = await ActionNode.from_pydantic(ReviseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

class Ensemble(Operator):

    def __init__(self, name:str ="Ensembler", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, solutions:List, problem_description):
        solution_text = ""
        for solution in solutions:
            solution_text += solution + "\n"
        prompt = ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem_description)
        node = await ActionNode.from_pydantic(EnsembleOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response