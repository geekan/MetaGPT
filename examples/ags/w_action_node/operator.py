# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 17:36 PM
# @Author  : didi
# @Desc    : operator demo of ags

import random
from typing import List, Tuple, Any, Dict
from collections import Counter

from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM 

from examples.ags.w_action_node.operator_an import GenerateOp, GenerateCodeOp, GenerateCodeBlockOp ,ReviewOp, ReviseOp, EnsembleOp, MdEnsembleOp
from examples.ags.w_action_node.prompt import GENERATE_PROMPT, GENERATE_CODE_PROMPT, REVIEW_PROMPT, REVISE_PROMPT, ENSEMBLE_PROMPT, MD_ENSEMBLE_PROMPT

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
    
class GenerateCodeBlock(Operator):

    def __init__(self, name:str ="Coder", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description):
        prompt = GENERATE_CODE_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(GenerateCodeBlockOp).fill(context=prompt, llm=self.llm,mode='code_fill')
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
            solution_text += str(solution) + "\n"
        prompt = ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem_description)
        node = await ActionNode.from_pydantic(EnsembleOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response
    
class MdEnsemble(Ensemble):

    def __init__(self, name:str ="MdEnsembler", llm: LLM = LLM(), vote_count:int=3):
        super().__init__(name, llm)
        self.vote_count = vote_count
    
    @staticmethod
    def shuffle_answers(solutions: List[str]) -> Tuple[List[str], Dict[str, str]]:
        shuffled_solutions = solutions.copy()
        random.shuffle(shuffled_solutions)
        answer_mapping = {
            chr(65 + i): solutions.index(sol)
            for i, sol in enumerate(shuffled_solutions)
        }
        return shuffled_solutions, answer_mapping
    
    @staticmethod
    def most_frequent(lst: List[Any]) -> Tuple[Any, int]:
        counter = Counter(lst)
        most_common = counter.most_common(1)
        return most_common[0] if most_common else (None, 0)

    async def __call__(self, solutions:List[str], problem_description:str,):
        all_responses = []

        for _ in range(self.vote_count):
            shuffled_solutions, answer_mapping = self.shuffle_answers(solutions)
            
            solution_text = ""
            for index, solution in enumerate(shuffled_solutions):
                solution_text += f"{chr(65 + index)}: {str(solution)}\n"
    
            prompt = MD_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem_description)
            node = await ActionNode.from_pydantic(MdEnsembleOp).fill(context=prompt, llm=self.llm)
            response = node.instruct_content.model_dump()
            
            answer = response.get('solution_letter', '')  
            answer = answer.strip().upper()
            
            if answer in answer_mapping:
                original_index = answer_mapping[answer]
                all_responses.append(solutions[original_index])
            
        final_answer, frequency = self.most_frequent(all_responses)
        
        return {"final_solution": final_answer}










# def load_llm_configs(*config_names):
#     """
#     Load multiple LLM configurations and return a list of initialized LLMs.

#     :param config_names: Variable number of configuration file names (without .yaml extension)
#     :return: List of initialized LLM objects
#     """
#     llms = []
#     for config_name in config_names:
#         config_path = Path(f"~/.metagpt/{config_name}.yaml").expanduser()
#         if config_path.exists():
#             config = Config.from_yaml_file(config_path)
#             llms.append(LLM(config.llm))
#         else:
#             print(f"Warning: Configuration file {config_path} not found. Skipping.")
#     return llms


# 使用函数加载多个 LLM 配置
# llms = load_llm_configs("gpt-4o", "sonnet-35")  # 你可以根据需要添加或删除配置