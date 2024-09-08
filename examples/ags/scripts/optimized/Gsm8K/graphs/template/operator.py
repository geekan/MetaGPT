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

from examples.ags.scripts.optimized.Gsm8K.graphs.template.op_prompt import *
from examples.ags.scripts.optimized.Gsm8K.graphs.template.operator_an import *
from examples.ags.scripts.utils import test_case_2_test_function
from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM
from metagpt.logs import logger


class Operator:
    def __init__(self, name, llm: LLM):
        self.name = name
        self.llm = llm

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class Custom(Operator):
    def __init__(self, llm: LLM, name: str = "Custom"):
        super().__init__(name, llm)

    async def __call__(self, input, instruction):
        prompt = input + instruction
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm, mode="single_fill")
        response = node.instruct_content.model_dump()
        return response


class Generate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem):
        prompt = GENERATE_PROMPT.format(problem_description=problem)
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm, mode="single_fill")
        response = node.instruct_content.model_dump()
        return response


class ContextualGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "ContextualGenerate"):
        super().__init__(name, llm)

    @retry(stop=stop_after_attempt(3))
    async def __call__(self, problem, context):
        prompt = CONTEXTUAL_GENERATE_PROMPT.format(problem_description=problem, thought=context)
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm, mode="single_fill")
        response = node.instruct_content.model_dump()
        return response


class CodeGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "CodeGenerate"):
        super().__init__(name, llm)

    @retry(stop=stop_after_attempt(3))
    async def __call__(self, problem, function_name):
        prompt = GENERATE_CODEBLOCK_PROMPT.format(problem_description=problem)
        node = await ActionNode.from_pydantic(CodeGenerateOp).fill(
            context=prompt, llm=self.llm, mode="code_fill", function_name=function_name
        )
        response = node.instruct_content.model_dump()
        return response  # {"code": "xxx"}


class CodeContextualGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "CodeContextualGenerate"):
        super().__init__(name, llm)

    @retry(stop=stop_after_attempt(3))
    async def __call__(self, problem, thought, function_name):
        prompt = CODE_CONTEXTUAL_GENERATE_PROMPT.format(problem_description=problem, thought=thought)
        node = await ActionNode.from_pydantic(CodeGenerateOp).fill(
            context=prompt, llm=self.llm, mode="code_fill", function_name=function_name
        )
        response = node.instruct_content.model_dump()
        return response  # {"code": "xxx"}


class Format(Operator):
    def __init__(self, llm: LLM, name: str = "Format"):
        super().__init__(name, llm)

    # 使用JSON MODE 输出 Formatted 的结果
    async def __call__(self, problem, solution):
        prompt = FORMAT_PROMPT.format(problem_description=problem, solution=solution)
        node = await ActionNode.from_pydantic(FormatOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response  # {"solution":"xxx"}


class Review(Operator):
    def __init__(self, llm: LLM, criteria: str = "accuracy", name: str = "Review"):
        self.criteria = criteria
        super().__init__(name, llm)

    async def __call__(self, problem, solution):
        prompt = REVIEW_PROMPT.format(problem_description=problem, solution=solution, criteria=self.criteria)
        node = await ActionNode.from_pydantic(ReviewOp).fill(context=prompt, llm=self.llm, mode="context_fill")
        response = node.instruct_content.model_dump()
        return response  # {"review_result": True, "feedback": "xxx"}


class Revise(Operator):
    def __init__(self, llm: LLM, name: str = "Revise"):
        super().__init__(name, llm)

    async def __call__(self, problem, solution, feedback):
        prompt = REVISE_PROMPT.format(problem_description=problem, solution=solution, feedback=feedback)
        node = await ActionNode.from_pydantic(ReviseOp).fill(context=prompt, llm=self.llm, mode="single_fill")
        response = node.instruct_content.model_dump()
        return response  # {"solution": "xxx"}


class FuEnsemble(Operator):
    """
    Function: Critically evaluating multiple solution candidates, synthesizing their strengths, and developing an enhanced, integrated solution.
    """

    def __init__(self, llm: LLM, name: str = "FuEnsemble"):
        super().__init__(name, llm)

    async def __call__(self, solutions: List, problem):
        solution_text = ""
        for solution in solutions:
            solution_text += str(solution) + "\n"
        prompt = FU_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem)
        node = await ActionNode.from_pydantic(FuEnsembleOp).fill(context=prompt, llm=self.llm, mode="context_fill")
        response = node.instruct_content.model_dump()
        return {"solution": response["final_solution"]}  # {"final_solution": "xxx"}


class MdEnsemble(Operator):
    """
    Paper: Can Generalist Foundation Models Outcompete Special-Purpose Tuning? Case Study in Medicine
    Link: https://arxiv.org/abs/2311.16452
    """

    def __init__(self, llm: LLM, name: str = "MdEnsemble", vote_count: int = 3):
        super().__init__(name, llm)
        self.vote_count = vote_count

    @staticmethod
    def shuffle_answers(solutions: List[str]) -> Tuple[List[str], Dict[str, str]]:
        shuffled_solutions = solutions.copy()
        random.shuffle(shuffled_solutions)
        answer_mapping = {chr(65 + i): solutions.index(solution) for i, solution in enumerate(shuffled_solutions)}
        return shuffled_solutions, answer_mapping

    async def __call__(self, solutions: List[str], problem: str):
        print(f"solution count: {len(solutions)}")
        all_responses = []

        for _ in range(self.vote_count):
            shuffled_solutions, answer_mapping = self.shuffle_answers(solutions)

            solution_text = ""
            for index, solution in enumerate(shuffled_solutions):
                solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

            prompt = MD_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem)
            node = await ActionNode.from_pydantic(MdEnsembleOp).fill(context=prompt, llm=self.llm, mode="context_fill")
            response = node.instruct_content.model_dump()

            answer = response.get("solution_letter", "")
            answer = answer.strip().upper()

            if answer in answer_mapping:
                original_index = answer_mapping[answer]
                all_responses.append(original_index)

        most_frequent_index = Counter(all_responses).most_common(1)[0][0]
        final_answer = solutions[most_frequent_index]
        return {"solution": final_answer}  # {"final_solution": "xxx"}


class CodeEnsmble(Operator):
    def __init__(self, llm: LLM, name: str = "CodeEnsemble", vote_count: int = 3):
        super().__init__(name, llm)
        self.vote_count = vote_count

    @staticmethod
    def shuffle_answers(solutions: List[dict]) -> Tuple[List[str], Dict[str, str]]:
        shuffled_solutions = solutions.copy()
        random.shuffle(shuffled_solutions)
        answer_mapping = {chr(65 + i): solutions.index(solution) for i, solution in enumerate(shuffled_solutions)}
        return shuffled_solutions, answer_mapping

    async def __call__(self, solutions: List[str], problem: str):
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

            prompt = MD_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem)
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
        return {"solution": final_answer}  # {"final_solution": "xxx"}


class ScEnsemble(Operator):
    """
    Paper: Self-Consistency Improves Chain of Thought Reasoning in Language Models
    Link: https://arxiv.org/abs/2203.11171
    Paper: Universal Self-Consistency for Large Language Model Generation
    Link: https://arxiv.org/abs/2311.17311
    """

    def __init__(self, llm: LLM, name: str = "ScEnsemble"):
        super().__init__(name, llm)

    async def __call__(self, solutions: List[str], problem: str):
        answer_mapping = {}
        solution_text = ""
        for index, solution in enumerate(solutions):
            answer_mapping[chr(65 + index)] = index
            solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

        prompt = SC_ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem)
        node = await ActionNode.from_pydantic(ScEnsembleOp).fill(context=prompt, llm=self.llm, mode="context_fill")
        response = node.instruct_content.model_dump()

        answer = response.get("solution_letter", "")
        answer = answer.strip().upper()

        return {"solution": solutions[answer_mapping[answer]]}  # {"final_solution": "xxx"}


class Rephrase(Operator):
    """
    Paper: Code Generation with AlphaCodium: From Prompt Engineering to Flow Engineering
    Link: https://arxiv.org/abs/2404.14963
    Paper: Achieving >97% on GSM8K: Deeply Understanding the Problems Makes LLMs Better Solvers for Math Word Problems
    Link: https://arxiv.org/abs/2404.14963
    """

    def __init__(self, llm: LLM, name: str = "Rephrase"):
        super().__init__(name, llm)

    async def __call__(self, problem: str) -> str:
        prompt = REPHRASE_ON_PROBLEM_PROMPT.format(problem_description=problem)
        node = await ActionNode.from_pydantic(RephraseOp).fill(context=prompt, llm=self.llm, mode="single_fill")
        response = node.instruct_content.model_dump()
        return response  # {"rephrased_problem": "xxx"}


class Test(Operator):
    def __init__(self, llm: LLM, name: str = "Test"):
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

    async def __call__(
        self, problem_id, problem, rephrase_problem, solution, test_cases, entry_point, test_loop: int = 3
    ):
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

        return {"solution": solution}
