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

from examples.ags.w_action_node.operator_an import GenerateOp, GenerateCodeOp, GenerateCodeBlockOp ,ReviewOp, ReviseOp, FuEnsembleOp, MdEnsembleOp, ReflectionTestOp, RephraseOp
from examples.ags.w_action_node.prompt import GENERATE_PROMPT, GENERATE_CODE_PROMPT, GENERATE_CODEBLOCK_PROMPT, REVIEW_PROMPT, REVISE_PROMPT, FU_ENSEMBLE_PROMPT, MD_ENSEMBLE_PROMPT, REFLECTION_ON_PUBILIC_TEST_PROMPT, REPHRASE_ON_PROBLEM_PROMPT, GENERATE_CODEBLOCK_REPHRASE_PROMPT 
from examples.ags.w_action_node.prompt import DE_ENSEMBLE_CODE_FORMAT_PROMPT, DE_ENSEMBLE_TXT_FORMAT_PROMPT, DE_ENSEMBLE_ANGEL_PROMPT, DE_ENSEMBLE_DEVIL_PROMPT, DE_ENSEMBLE_JUDGE_UNIVERSAL_PROMPT, DE_ENSEMBLE_JUDGE_FINAL_PROMPT
from examples.ags.w_action_node.utils import test_cases_2_test_functions

class Operator:
    def __init__(self, name, llm:LLM):
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

    async def __call__(self, problem_description, function_name):
        prompt = GENERATE_CODEBLOCK_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(GenerateCodeBlockOp).fill(context=prompt, llm=self.llm, mode='code_fill',function_name=function_name)
        response = node.instruct_content.model_dump()
        return response

    async def rephrase_generate(self, problem_description, rephrase_problem, function_name):
        prompt = GENERATE_CODEBLOCK_REPHRASE_PROMPT.format(problem_description=problem_description,rephrase_problem=rephrase_problem)
        node = await ActionNode.from_pydantic(GenerateCodeBlockOp).fill(context=prompt, llm=self.llm, mode='code_fill', function_name=function_name)
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

class FuEnsemble(Operator):

    def __init__(self, name:str ="FuseEnsembler", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, solutions:List, problem_description):
        solution_text = ""
        for solution in solutions:
            solution_text += str(solution) + "\n"
        prompt = FU_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem_description)
        node = await ActionNode.from_pydantic(FuEnsembleOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response
    
class MdEnsemble(Operator):
    """
    MedPrompt
     
    """
    def __init__(self, name:str ="MedEnsembler", llm: LLM = LLM(), vote_count:int=3):
        super().__init__(name, llm)
        self.vote_count = vote_count
    
    @staticmethod
    def shuffle_answers(solutions: List[str]) -> Tuple[List[str], Dict[str, str]]:
        shuffled_solutions = solutions.copy()
        random.shuffle(shuffled_solutions)
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
            # print(f"Original number of solutions: {original_length}")
            # print(f"Updated number of solutions: {updated_length}")
            if updated_length == 1:
                return {"final_solution": solutions[0]}
        for _ in range(self.vote_count):
            shuffled_solutions, answer_mapping = self.shuffle_answers(solutions)
            
            solution_text = ""
            for index, solution in enumerate(shuffled_solutions):
                solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"
    
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
        print(f"final answer: \n{final_answer}")
        # final_answer, frequency = self.most_frequent(all_responses)
        return {"final_solution": final_answer}

class ScEnsemble(Operator):
    """
    self consistency ensemble
    """

    # ScEnsemble 的构建相对好做一点 30分钟左右
    pass

class DbEnsemble(Operator):
    """
    (Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs)
    The system is a multi-round debate system where each agent is given the
    question and responses generated by all agents. For each round, a judge
    analyzes the responses provided determines whether to terminate the
    debate or keep going. At the end of the debate the judge is also responsible
    for determining the final answer.
    """
    def __init__(self, name:str ="DebateEnsemble", llm: LLM = LLM()):
        super().__init__(name, llm)
        self.agents = ["angel","devil","judge"]
        self.format_requirements = {
            "txt":DE_ENSEMBLE_TXT_FORMAT_PROMPT,
            "code":DE_ENSEMBLE_CODE_FORMAT_PROMPT
        }
    
    def get_system_prompt(self, name:str, mode:str='txt'):
        if name == "angel":
            if mode == "code":
                return DE_ENSEMBLE_ANGEL_PROMPT + "\n" + DE_ENSEMBLE_CODE_FORMAT_PROMPT
            return DE_ENSEMBLE_ANGEL_PROMPT + "\n" + DE_ENSEMBLE_TXT_FORMAT_PROMPT
        elif name == "devil":
            if mode == "code":
                return DE_ENSEMBLE_DEVIL_PROMPT + "\n" + DE_ENSEMBLE_CODE_FORMAT_PROMPT
            return DE_ENSEMBLE_DEVIL_PROMPT + "\n" + DE_ENSEMBLE_TXT_FORMAT_PROMPT
        elif name == "judge":
            if mode == "final":
                return DE_ENSEMBLE_JUDGE_FINAL_PROMPT 
            return DE_ENSEMBLE_JUDGE_UNIVERSAL_PROMPT
            
    def construct_messages(self, message_history_with_name, name, mode:str="txt", phase:str="universal"):
        """
        基于name与mode来构建system message.
        基于name来构建messages
        """
        messages = []
        messages.append({"role": "system", "content": self.get_system_prompt(name, mode)})

        if name in ["angel", "devil"]:
            messages = self._construct_debate(message_history_with_name, name, messages)
        elif name == "judge":
            messages = self._construct_judge(message_history_with_name, mode, messages)
        return messages
    
    def _construct_debate(self, message_history_with_name, name, messages):
        user_message = ""
        
        for message in message_history_with_name:
            if message["name"] == "Judge":
                continue
            elif message["name"] == name:
                if user_message:
                    messages.append({
                        "role": "user",
                        "name": "user",
                        "content": user_message.strip("\n"),
                    })
                messages.append({
                    "role": "assistant",
                    "name": name,
                    "content": message["content"],
                })
                user_message = ""
            else:
                user_message += message["content"]
        
        if user_message:
            messages.append({
                "role": "user",
                "name": "user",
                "content": user_message.strip("\n"),
            })
        
        return messages

    def _construct_judge(self, message_history_with_name, mode, messages):
        pass

    async def debate_answer(self, message_history:List, role:str="angel"):
        messages = self.construct_messages(message_history, role)
        response = await self.llm.acompletion_text(messages=messages)
        message_history.append({
            "role":"user",
            "name":role,
            "content":response}
        )   
        return message_history, response

    async def judge_answer(self, message_history:List, phase:str="universal"):
        messages = self.construct_messages(message_history, "judge", phase=phase)
        response = await self.llm.acompletion_text(messages=messages)
        message_history.append({
            "role": "user",
            "name": "judge",
            "content": response}
        )
        return message_history, response

    async def __call__(self, origin_solution:str, problem_description:str, max_round:int = 3, mode:str='txt'):
        # 思路，输入一个原始答案，构建一个agent代表这个答案进行辩论；另一个agent（devil）使用debate llm的内容进行辩论；法官在每一轮次做出决定是否终止，到了maxround还没终止就由法官进行总结。
        message_history_with_name = [
            {"role":"user", "name":"angel", "content":origin_solution}
        ]
        
        for index in range(max_round):
            for agent in self.agents:
                if agent == "angel":
                    if index == 0:
                        pass
                    message_history_with_name, rsp = self.debate_answer(message_history_with_name, role="angel")
                elif agent == "devil":
                    message_history_with_name, rsp = self.debate_answer(message_history_with_name, role="devil")
                elif agent == "judge":
                    message_history_with_name, judge_result = self.judge_answer(message_history_with_name, phase="universal")
                    if not judge_result["is_debating"]:
                        """
                        这里需要在 self.judge_answer 中设置一个自动给出solution的地方
                        """
                        return {"final_solution":judge_result["final_solution"]}
        
        message_history_with_name.pop(-1)
        message_history_with_name, judge_answer  = self.judge_answer(message_history_with_name, phase="final")

        return {"final_solution":judge_answer["debate_answer"]}

class Rephrase(Operator):
    """
    1. AlphaCodium
    2. https://arxiv.org/abs/2404.14963
    """
    def __init__(self, name:str ="Rephraser", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description:str)->str:
        prompt = REPHRASE_ON_PROBLEM_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response["rephrased_problem"]
        
class Test(Operator):
    def __init__(self, name:str ="Tester", llm: LLM = LLM()):
        super().__init__(name, llm)

    def test_cases_2_assert(self, test_cases):
        return f"assert {test_cases[0]}({test_cases[1]}) == {test_cases[2]} \n"
    
    def exec_code(self, solution, test_cases):
        solution = solution["final_solution"]
        pass_case = []
        fail_case = []
        for test_case in test_cases:
            test_code = test_cases_2_test_functions(solution,test_case)
            try:
                exec(test_code)
                pass_case.append(self.test_cases_2_assert(test_case))
            except AssertionError as e:
                fail_case.append(self.test_cases_2_assert(test_case))
            except Exception as e:
                with open("tester.txt", "a") as f:
                    f.write(test_case[0] + "\n")
                print(e)
                return {"error":e}
        if fail_case != []:
            return fail_case
        return []

    async def __call__(self, problem, rephrase_problem, solution, test_cases):
        result = self.exec_code(solution, test_cases)
        # 处理通过Public Tests的代码
        # TODO 这里的问题是，如果Test直接通过了就没有办法Check Multi Tests了
        if result == []:
            return solution
        # 处理代码执行失败的代码
        elif type(result) == dict:
            result = result["error"]
            prompt = REFLECTION_ON_PUBILIC_TEST_PROMPT.format(problem_description=problem, rephrase_problem=rephrase_problem, code_solution=solution, exec_pass=f"executed unsuccessfully, error: \n {result}", test_fail="executed unsucessfully")
            node = await ActionNode.from_pydantic(ReflectionTestOp).fill(context=prompt, llm=self.llm)
            response = node.instruct_content.model_dump()
            return {"final_solution":response["refined_solution"]}
        else:
            prompt = REFLECTION_ON_PUBILIC_TEST_PROMPT.format(problem_description=problem, rephrase_problem=rephrase_problem, code_solution=solution, exec_pass="executed successfully", test_fail=result)
            node = await ActionNode.from_pydantic(ReflectionTestOp).fill(context=prompt, llm=self.llm)
            response = node.instruct_content.model_dump()
            return {"final_solution":response["refined_solution"]}
            
class FindFact(Operator):
    pass

class SelfAsk(Operator):
    pass

class Verify(Operator):
    """
    ? 还没有想好
    """
    pass

