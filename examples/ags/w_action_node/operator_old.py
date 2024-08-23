# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 17:36 PM
# @Author  : didi
# @Desc    : operator demo of ags
import ast
import random
import sys
import traceback
from collections import Counter
from typing import Dict, List, Tuple

from tenacity import retry, stop_after_attempt

from examples.ags.w_action_node.operator_an import (
    FormatOp,
    FuEnsembleOp,
    GenerateCodeBlockOp,
    GenerateCodeSolution,
    GenerateOp,
    MdEnsembleOp,
    ReflectionTestOp,
    RephraseOp,
    ReviewOp,
    ReviseOp,
)
from examples.ags.w_action_node.prompt import (
    DE_ENSEMBLE_ANGEL_PROMPT,
    DE_ENSEMBLE_CODE_FORMAT_PROMPT,
    DE_ENSEMBLE_DEVIL_PROMPT,
    DE_ENSEMBLE_JUDGE_FINAL_PROMPT,
    DE_ENSEMBLE_JUDGE_UNIVERSAL_PROMPT,
    DE_ENSEMBLE_TXT_FORMAT_PROMPT,
    FORMAT_PROMPT,
    FU_ENSEMBLE_PROMPT,
    GENERATE_CODE_SOLUTION_PROMPT,
    GENERATE_CODEBLOCK_PROMPT,
    GENERATE_CODEBLOCK_REPHRASE_PROMPT,
    GENERATE_ON_CONTEXT_PROMPT,
    GENERATE_PROMPT,
    MATH_ANSWER_FORMAT_PROMPT,
    MATH_CORE_PROMPT,
    MATH_EXTRACT_PROMPT,
    MATH_GENERATE_PROMPT,
    MATH_REPHRASE_ON_PROBLEM_PROMPT,
    MD_ENSEMBLE_PROMPT,
    REFLECTION_ON_PUBLIC_TEST_PROMPT,
    REPHRASE_ON_CODE_PROMPT,
    REPHRASE_ON_PROBLEM_PROMPT,
    REVIEW_PROMPT,
    REVISE_PROMPT,
)
from examples.ags.w_action_node.utils import test_case_2_test_function
from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM
from metagpt.logs import logger


class Operator:
    def __init__(self, name, llm: LLM):
        self.name = name
        self.llm = llm

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class Generate(Operator):
    """
    基于Action Node Fill Function的 Generate 算子
    """

    def __init__(self, name: str = "Generate", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description):
        prompt = GENERATE_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

    async def math_generate(self, problem_description):
        prompt = MATH_GENERATE_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

    async def code_solution_generate(self, problem_description: str, rephrase_problem: str):
        prompt = GENERATE_CODE_SOLUTION_PROMPT.format(
            problem_description=problem_description, rephrase_problem=rephrase_problem
        )
        node = await ActionNode.from_pydantic(GenerateCodeSolution).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

    async def context_solution_generate(self, question, context):
        prompt = GENERATE_ON_CONTEXT_PROMPT.format(problem_description=question, context=context)
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response


class GenerateCodeBlock(Operator):
    def __init__(self, name: str = "GenerateCodeBlock", llm: LLM = LLM()):
        super().__init__(name, llm)

    @retry(stop=stop_after_attempt(3))
    async def __call__(self, problem_description, function_name):
        prompt = GENERATE_CODEBLOCK_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(GenerateCodeBlockOp).fill(
            context=prompt, llm=self.llm, mode="code_fill", function_name=function_name
        )
        response = node.instruct_content.model_dump()
        return response

    @retry(stop=stop_after_attempt(3))
    async def rephrase_generate(self, problem_description, thought, function_name):
        prompt = GENERATE_CODEBLOCK_REPHRASE_PROMPT.format(problem_description=problem_description, thought=thought)
        node = await ActionNode.from_pydantic(GenerateCodeBlockOp).fill(
            context=prompt, llm=self.llm, mode="code_fill", function_name=function_name
        )
        response = node.instruct_content.model_dump()
        return response


class Format(Operator):
    def __init__(self, name: str = "Format", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description, solution):
        prompt = FORMAT_PROMPT.format(problem_description=problem_description, solution=solution)
        node = await ActionNode.from_pydantic(FormatOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

    async def math_answer_format(self, problem_description: str) -> dict:
        prompt = MATH_ANSWER_FORMAT_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(FormatOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response


class Review(Operator):
    def __init__(self, criteria, name: str = "Review", llm: LLM = LLM()):
        self.criteria = criteria
        super().__init__(name, llm)

    async def __call__(self, problem_description, solution):
        prompt = REVIEW_PROMPT.format(
            problem_description=problem_description, solution=solution, criteria=self.criteria
        )
        node = await ActionNode.from_pydantic(ReviewOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response


class Revise(Operator):
    def __init__(self, name: str = "Revise", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description, solution, feedback):
        prompt = REVISE_PROMPT.format(problem_description=problem_description, solution=solution, feedback=feedback)
        node = await ActionNode.from_pydantic(ReviseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response


class FuEnsemble(Operator):
    """
    Function: Critically evaluating multiple solution candidates, synthesizing their strengths, and developing an enhanced, integrated solution.
    """

    def __init__(self, name: str = "FuEnsemble", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, solutions: List, problem_description):
        solution_text = ""
        for solution in solutions:
            solution_text += str(solution) + "\n"
        prompt = FU_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem_description)
        node = await ActionNode.from_pydantic(FuEnsembleOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response


class MdEnsemble(Operator):
    """
    Paper: Can Generalist Foundation Models Outcompete Special-Purpose Tuning? Case Study in Medicine
    Link: https://arxiv.org/abs/2311.16452
    """

    def __init__(self, name: str = "MdEnsemble", llm: LLM = LLM(), vote_count: int = 3):
        super().__init__(name, llm)
        self.vote_count = vote_count

    @staticmethod
    def shuffle_answers(solutions: List[str]) -> Tuple[List[str], Dict[str, str]]:
        shuffled_solutions = solutions.copy()
        random.shuffle(shuffled_solutions)
        answer_mapping = {chr(65 + i): solutions.index(solution) for i, solution in enumerate(shuffled_solutions)}
        return shuffled_solutions, answer_mapping

    async def __call__(self, solutions: List[str], problem_description: str):
        print(f"solution count: {len(solutions)}")
        all_responses = []

        for _ in range(self.vote_count):
            shuffled_solutions, answer_mapping = self.shuffle_answers(solutions)

            solution_text = ""
            for index, solution in enumerate(shuffled_solutions):
                solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

            prompt = MD_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem_description)
            node = await ActionNode.from_pydantic(MdEnsembleOp).fill(context=prompt, llm=self.llm)
            response = node.instruct_content.model_dump()

            answer = response.get("solution_letter", "")
            answer = answer.strip().upper()

            if answer in answer_mapping:
                original_index = answer_mapping[answer]
                all_responses.append(original_index)

        most_frequent_index = Counter(all_responses).most_common(1)[0][0]
        final_answer = solutions[most_frequent_index]
        return {"final_solution": final_answer}


class CodeEnsmble(Operator):
    def __init__(self, name: str = "CodeEnsemble", llm: LLM = LLM(), vote_count: int = 3):
        super().__init__(name, llm)
        self.vote_count = vote_count

    @staticmethod
    def shuffle_answers(solutions: List[dict]) -> Tuple[List[str], Dict[str, str]]:
        shuffled_solutions = solutions.copy()
        random.shuffle(shuffled_solutions)
        answer_mapping = {chr(65 + i): solutions.index(solution) for i, solution in enumerate(shuffled_solutions)}
        return shuffled_solutions, answer_mapping

    async def __call__(self, solutions: List[str], problem_description: str):
        all_responses = []

        unique_structures = {}
        unique_structures_count = {}

        valid_solutions_count = 0  # 添加计数器来跟踪有效的解决方案数量

        for solution in solutions:
            try:
                tree = ast.parse(solution)
                structure_key = ast.dump(tree, annotate_fields=False, include_attributes=False)

                if structure_key not in unique_structures:
                    unique_structures[structure_key] = solution
                    unique_structures_count[structure_key] = 1
                else:
                    unique_structures_count[structure_key] += 1

                valid_solutions_count += 1  # 增加有效解决方案的计数
            except SyntaxError:
                # 剔除语法错误的代码
                continue

        solutions = [
            {"code": unique_structures[structure_key], "weight": count / valid_solutions_count}  # 使用有效解决方案的数量来计算权重
            for structure_key, count in unique_structures_count.items()
        ]

        updated_length = len(solutions)
        if updated_length == 1:
            return {"final_solution": solutions[0]["code"]}

        for _ in range(self.vote_count):
            shuffled_solutions, answer_mapping = self.shuffle_answers(solutions)

            solution_text = ""
            for index, solution in enumerate(shuffled_solutions):
                weight = str(solution["weight"])
                code = solution["code"]
                solution_text += (
                    f"{chr(65 + index)}: \n weight(proportion of occurrences in all solutions):{weight} \n{code}\n\n\n"
                )

            prompt = MD_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem_description)
            node = await ActionNode.from_pydantic(MdEnsembleOp).fill(context=prompt, llm=self.llm)
            response = node.instruct_content.model_dump()

            answer = response.get("solution_letter", "")
            answer = answer.strip().upper()

            if answer in answer_mapping:
                original_index = answer_mapping[answer]
                # print(f"original index: {original_index}")
                all_responses.append(original_index)

        most_frequent_index = Counter(all_responses).most_common(1)[0][0]
        final_answer = solutions[most_frequent_index]["code"]
        return {"final_solution": final_answer}


class ScEnsemble(Operator):
    """
    Paper: Self-Consistency Improves Chain of Thought Reasoning in Language Models
    Link: https://arxiv.org/abs/2203.11171
    """

    pass


class MADEnsemble(Operator):
    """
    Paper: Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs
    Link: https://arxiv.org/abs/2311.17371
    """

    def __init__(self, name: str = "DebateEnsemble", llm: LLM = LLM()):
        super().__init__(name, llm)
        self.agents = ["angel", "devil", "judge"]
        self.format_requirements = {"txt": DE_ENSEMBLE_TXT_FORMAT_PROMPT, "code": DE_ENSEMBLE_CODE_FORMAT_PROMPT}

    def get_system_prompt(self, name: str, mode: str = "txt"):
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

    def construct_messages(self, message_history_with_name, name, mode: str = "txt", phase: str = "universal"):
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
                    messages.append(
                        {
                            "role": "user",
                            "name": "user",
                            "content": user_message.strip("\n"),
                        }
                    )
                messages.append(
                    {
                        "role": "assistant",
                        "name": name,
                        "content": message["content"],
                    }
                )
                user_message = ""
            else:
                user_message += message["content"]

        if user_message:
            messages.append(
                {
                    "role": "user",
                    "name": "user",
                    "content": user_message.strip("\n"),
                }
            )

        return messages

    def _construct_judge(self, message_history_with_name, mode, messages):
        pass

    async def debate_answer(self, message_history: List, role: str = "angel"):
        messages = self.construct_messages(message_history, role)
        response = await self.llm.acompletion_text(messages=messages)
        message_history.append({"role": "user", "name": role, "content": response})
        return message_history, response

    async def judge_answer(self, message_history: List, phase: str = "universal"):
        messages = self.construct_messages(message_history, "judge", phase=phase)
        response = await self.llm.acompletion_text(messages=messages)
        message_history.append({"role": "user", "name": "judge", "content": response})
        return message_history, response

    async def __call__(self, origin_solution: str, problem_description: str, max_round: int = 3, mode: str = "txt"):
        # 思路，输入一个原始答案，构建一个agent代表这个答案进行辩论；另一个agent（devil）使用debate llm的内容进行辩论；法官在每一轮次做出决定是否终止，到了maxround还没终止就由法官进行总结。
        message_history_with_name = [{"role": "user", "name": "angel", "content": origin_solution}]

        for index in range(max_round):
            for agent in self.agents:
                if agent == "angel":
                    if index == 0:
                        pass
                    message_history_with_name, rsp = self.debate_answer(message_history_with_name, role="angel")
                elif agent == "devil":
                    message_history_with_name, rsp = self.debate_answer(message_history_with_name, role="devil")
                elif agent == "judge":
                    message_history_with_name, judge_result = self.judge_answer(
                        message_history_with_name, phase="universal"
                    )
                    if not judge_result["is_debating"]:
                        """
                        这里需要在 self.judge_answer 中设置一个自动给出solution的地方
                        """
                        return {"final_solution": judge_result["final_solution"]}

        message_history_with_name.pop(-1)
        message_history_with_name, judge_answer = self.judge_answer(message_history_with_name, phase="final")

        return {"final_solution": judge_answer["debate_answer"]}


class Rephrase(Operator):
    """
    Paper: Code Generation with AlphaCodium: From Prompt Engineering to Flow Engineering
    Link: https://arxiv.org/abs/2404.14963
    Paper: Achieving >97% on GSM8K: Deeply Understanding the Problems Makes LLMs Better Solvers for Math Word Problems
    Link: https://arxiv.org/abs/2404.14963
    """

    def __init__(self, name: str = "Rephrase", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem_description: str) -> str:
        prompt = REPHRASE_ON_PROBLEM_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response["rephrased_problem"]

    async def code_rephrase(self, problem_description: str) -> str:
        prompt = REPHRASE_ON_CODE_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response["rephrased_problem"]

    async def math_rephrase(self, problem_description: str) -> str:
        prompt = MATH_REPHRASE_ON_PROBLEM_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response["rephrased_problem"]

    async def math_core(self, problem_description: str) -> str:
        prompt = MATH_CORE_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response["rephrased_problem"]

    async def math_extract(self, problem_description: str) -> str:
        prompt = MATH_EXTRACT_PROMPT.format(problem_description=problem_description)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response["rephrased_problem"]


class Test(Operator):
    def __init__(self, name: str = "Test", llm: LLM = LLM()):
        super().__init__(name, llm)

    def exec_code(self, solution, test_cases, problem_id, entry_point):
        fail_cases = []
        for test_case in test_cases:
            test_code = test_case_2_test_function(solution, test_case, entry_point)
            try:
                exec(test_code, globals())
            except AssertionError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                tb_str = traceback.format_exception(exc_type, exc_value, exc_traceback)
                with open("tester.txt", "a") as f:
                    f.write("test_error" + problem_id + "\n")
                error_infomation = {
                    "test_fail_case": {
                        "test_case": test_case,
                        "error_type": "AssertionError",
                        "error_message": str(e),
                        "traceback": tb_str,
                    }
                }
                fail_cases.append(error_infomation)
                logger.info(f"test error: {error_infomation}")
            except Exception as e:
                with open("tester.txt", "a") as f:
                    f.write(problem_id + "\n")
                return {"exec_fail_case": str(e)}
        if fail_cases != []:
            return fail_cases
        else:
            return "no error"

    async def __call__(self, problem_id, problem, rephrase_problem, solution, test_cases, entry_point, test_loop):
        solution = solution["final_solution"]
        for _ in range(test_loop):
            result = self.exec_code(solution, test_cases, problem_id, entry_point)
            if result == "no error":
                return {"final_solution": solution}
            elif "exec_fail_case" in result:
                result = result["exec_fail_case"]
                prompt = REFLECTION_ON_PUBLIC_TEST_PROMPT.format(
                    problem_description=problem,
                    rephrase_problem=rephrase_problem,
                    code_solution=solution,
                    exec_pass=f"executed unsuccessfully, error: \n {result}",
                    test_fail="executed unsucessfully",
                )
                node = await ActionNode.from_pydantic(ReflectionTestOp).fill(context=prompt, llm=self.llm)
                response = node.instruct_content.model_dump()
                solution = response["refined_solution"]
            else:
                prompt = REFLECTION_ON_PUBLIC_TEST_PROMPT.format(
                    problem_description=problem,
                    rephrase_problem=rephrase_problem,
                    code_solution=solution,
                    exec_pass="executed successfully",
                    test_fail=result,
                )
                node = await ActionNode.from_pydantic(ReflectionTestOp).fill(context=prompt, llm=self.llm)
                response = node.instruct_content.model_dump()
                solution = response["refined_solution"]
        return {"final_solution": solution}


class FindFact(Operator):
    def __init__(self, name: str = "FindFact", llm: LLM = LLM()):
        super().__init__(name, llm)


class SelfAsk(Operator):
    def __init__(self, name: str = "SelfAsk", llm: LLM = LLM()):
        super().__init__(name, llm)


class Verify(Operator):
    def __init__(self, name: str = "Verify", llm: LLM = LLM()):
        super().__init__(name, llm)
