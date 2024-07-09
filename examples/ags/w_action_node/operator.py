# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 17:36 PM
# @Author  : didi
# @Desc    : operator demo of ags
import ast
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
    
class MdEnsemble(Operator):

    def __init__(self, name:str ="MdEnsembler", llm: LLM = LLM(), vote_count:int=3):
        super().__init__(name, llm)
        self.vote_count = vote_count
    
    @staticmethod
    def shuffle_answers(solutions: List[str]) -> Tuple[List[str], Dict[str, str]]:
        shuffled_solutions = solutions.copy()
        random.shuffle(shuffled_solutions)
        # 这里的index方法会把检索到的放在第一个索引的位置。
        answer_mapping = {chr(65 + i): solutions.index(solution) for i, solution in enumerate(shuffled_solutions)}
        return shuffled_solutions, answer_mapping

    async def __call__(self, solution_type:str ,solutions:List[str], problem_description:str):
        all_responses = []
        # 如果Solution方案是Code，我们利用AST去重
        if solution_type == "code":
            original_length = len(solutions)
            unique_structures = {}
            updated_solutions = []

            for solution in solutions:
                try:
                    tree = ast.parse(solution)
                    structure_key = ast.dump(tree, annotate_fields=False, include_attributes=False)
                    
                    if structure_key not in unique_structures:
                        unique_structures[structure_key] = solution
                        updated_solutions.append(solution)
                except SyntaxError:
                    # If the solution has a syntax error, we'll skip it
                    continue
            solutions = updated_solutions
            updated_length = len(solutions)
            print(f"Original number of solutions: {original_length}")
            print(f"Updated number of solutions: {updated_length}")
            if updated_length == 1:
                return {"final_solution": solutions[0]}
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
                print(f"original index: {original_index}")
                all_responses.append(original_index)
        
        most_frequent_index = Counter(all_responses).most_common(1)[0][0]
        print(f"most frequent_index: {most_frequent_index}") 
        final_answer = solutions[most_frequent_index]
        print(f"final answer: {final_answer}")
        # final_answer, frequency = self.most_frequent(all_responses)
        return {"final_solution": final_answer}

class ScEnsemble(Operator):
    # TODO
    pass