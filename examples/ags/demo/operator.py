# -*- coding: utf-8 -*-
# @Date    : 6/26/2024 17:07 PM
# @Author  : didi
# @Desc    : operator demo of ags

import json
from openai import OpenAI
from examples.ags.demo.prompt import GENERATE_PROMPT, GENERATE_CODE_PROMPT, REVIEW_PROMPT, REVISE_PROMPT, ENSEMBLE_PROMPT

class LLM():
    def __init__(self, model:str='gpt-4-turbo', timeout:int=60):
        self.model = model
        self.timeout = timeout
        self.api_key = 'sk-6uLg7KCASTHxoLIL00E0F0C0377449Bd9cE506B04791B23a'
        self.base_url = 'https://api.aigcbest.top/v1'
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.system_prompt = None

    def ask(self, text: str, json_mode: bool = False, temperature: float = 0.7, retries: int = 5):
        response_type = "text" if not json_mode else "json_object"
        messages = [{"role": "user", "content": text}] if self.system_prompt == None else [
            {"role": "system", "content": self.system_prompt}, {"role": "user", "content": text}]
        for i in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": response_type}
                )
                if json_mode:
                    result = response.choices[0].message.content
                    result = json.loads(result)
                else:
                    result = response.choices[0].message.content
                print(result)
                return result
            except Exception as e:
                print(f"{__name__} occurs: {e}")


class Operator:
    def __init__(self, name, llm:LLM=None):
        self.name = name
        self.llm = llm

    def __call__(self, *args, **kwargs):
        raise NotImplementedError

class Generate(Operator):
    """
    Generate code & Generate text 应该被分开
    """
    def __init__(self, name:str ="Generator", llm: LLM = LLM()):
        super().__init__(name, llm)

    def __call__(self, problem_description):
        prompt = GENERATE_PROMPT.format(problem_description=problem_description)
        response = self.llm.ask(prompt, json_mode=True)
        return {"solution": response.get("solution")}
    
class GenerateCode(Operator):

    def __init__(self, name:str ="Coder", llm: LLM = LLM()):
        super().__init__(name, llm)

    def __call__(self, problem_description):
        prompt = GENERATE_CODE_PROMPT.format(problem_description=problem_description)
        response = self.llm.ask(prompt, json_mode=True)
        return {"code": response.get("code")}
    
class Review(Operator):
    
    def __init__(self, criteria, name:str ="Reviewer", llm: LLM = LLM()):
        self.criteria = criteria
        super().__init__(name, llm)

    # TODO 有点搞笑，我忘记加上criteria了
    def __call__(self, problem_description, solution):
        prompt = REVIEW_PROMPT.format(problem_description=problem_description, solution=solution)
        response = self.llm.ask(prompt, json_mode=True)
        if response.get("result") == True:
            return {"result": True}
        else:
            return {"result":False, "feedback":response.get('feedback')}

class Revise(Operator):

    def __init__(self, name:str ="Reviser", llm: LLM = LLM()):
        super().__init__(name, llm)

    def __call__(self, problem_description, solution, feedback):
        prompt = REVISE_PROMPT.format(problem_description=problem_description, solution=solution, feedback=feedback)
        response = self.llm.ask(prompt, json_mode=True)
        return {"revised_solution": response.get("revised_solution")}

class Ensemble(Operator):

    def __init__(self, name:str ="Ensembler", llm: LLM = LLM()):
        super().__init__(name, llm)

    def __call__(self, *args, problem_description):
        solutions = ""
        for solution in args:
            solutions += solution + "\n"
        prompt = ENSEMBLE_PROMPT.format(solutions=solutions, problem_description=problem_description)
        response = self.llm.ask(prompt, json_mode=True)
        return {"ensembled_solution": response.get("ensembled_solution")}

