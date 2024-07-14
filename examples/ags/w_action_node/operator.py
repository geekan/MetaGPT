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

from examples.ags.w_action_node.operator_an import GenerateOp, GenerateCodeOp, GenerateCodeBlockOp ,ReviewOp, ReviseOp, FuEnsembleOp, MdEnsembleOp
from examples.ags.w_action_node.prompt import GENERATE_PROMPT, GENERATE_CODE_PROMPT, REVIEW_PROMPT, REVISE_PROMPT, FU_ENSEMBLE_PROMPT, MD_ENSEMBLE_PROMPT, DE_ENSEMBLE_ANGEL_PROMPT, DE_ENSEMBLE_DEVIL_PROMPT, DE_ENSEMBLE_JUDGE_PROMPT

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
        self.agents = [
        ]

    async def debate_answer(self, message_history:List, role:str):
        """
        async def lowlevel_api_example(llm: LLM):
            logger.info("low level api example")
            logger.info(await llm.aask_batch(["hi", "write python hello world."]))

            hello_msg = [{"role": "user", "content": "count from 1 to 10. split by newline."}]
            logger.info(await llm.acompletion(hello_msg))
            logger.info(await llm.acompletion_text(hello_msg))

            # streaming mode, much slower
            await llm.acompletion_text(hello_msg, stream=True)

            # check completion if exist to test llm complete functions
            if hasattr(llm, "completion"):
                logger.info(llm.completion(hello_msg))
        """
        if role == "angel":
            prompt = DE_ENSEMBLE_ANGEL_PROMPT.format()
            Op = ""
        else:
            prompt = DE_ENSEMBLE_DEVIL_PROMPT.format()
            Op = ""
        
        node = await ActionNode.from_pydantic(Op).messages_fill(messages=message_history,llm=self.llm)
        node = await ActionNode.from_pydantic(FuEnsembleOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

    async def judge_answer(message_histroy:List):
        """

        """
        pass

    async def __call__(self, origin_solution:str, problem_description:str, max_round:int = 3):
        # 思路，输入一个原始答案，构建一个agent代表这个答案进行辩论；另一个agent（devil）使用debate llm的内容进行辩论；法官在每一轮次做出决定是否终止，到了maxround还没终止就由法官进行总结。
        # 以下是调用llm的方法
        """
        1. judge信息只有法官自己看到
        2. agent answer信息所有人都能看到，具体代码逻辑在debate
        """
        # 在MG里面多轮对话传Message在哪里传，预计时间1小时左右吧

        angel_prompt = DE_ENSEMBLE_ANGEL_PROMPT.format()
        devil_prompt = DE_ENSEMBLE_DEVIL_PROMPT.format()
        judge_prompt = DE_ENSEMBLE_JUDGE_PROMPT.format()
        '''
            Devil
            You agree with my answer 90% of the time and have almost no reservations. Affirm your agreement, share any additional thoughts if you have them, and conclude with the capital letter corresponding to your answer at the end of your response.
            
            Angel
            Do you agree with my perspective? Please provide your reasons and answer.

            Judge
            final_mode: "You, as the moderator, will evaluate both sides' answers and determine your
            preference for an answer candidate. Please summarize your reasons for supporting affirmative/negative side and
            give the final answer that you think is correct to conclude the debate. Now please output your answer in json format, with the format as follows:
            {\"Reason\": \"\", \"debate_answer\": \"the capital letter corresponding to the answer\"}.
            Please strictly output in JSON format, do not output irrelevant content."

            universal_mode: "You, as the moderator, will evaluate both sides' answers and determine if there is a clear
            preference for an answer candidate. If so, please summarize your reasons for supporting affirmative/negative side and
            give the final answer that you think is correct, and the debate will conclude. If not, the debate will continue to
            the next round. Now please output your answer in json format, with the format as follows:
            {\"Whether there is a preference\": \"Yes or No\", \"Supported Side\": \"Affirmative or Negative\",
            \"Reason\": \"\", \"debate_answer\": \"the capital letter corresponding to the answer\"}.
            Please strictly output in JSON format, do not output irrelevant content."
        '''

        # 在action node 之中构建一个能够传递message history的方法。
        for _ in max_round:
            for agent in self.agents:
                pass

        node = await ActionNode.from_pydantic(FuEnsembleOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

class Rephrase(Operator):
    """

    https://arxiv.org/abs/2404.14963
    """
    pass

class FindFact(Operator):
    pass

class SelfAsk(Operator):
    pass

class CodeReflection(Operator):
    """
    Interpreter Part
    We run code here to get error information.
    """

class Verify(Operator):
    """
    ? 还没有想好
    """