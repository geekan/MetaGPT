# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 22:07 PM
# @Author  : didi
# @Desc    : graph & an instance - humanevalgraph

from typing import List

from evalplus.data import get_human_eval_plus

from examples.ags.w_action_node.operator import (
    CodeEnsmble,
    Format,
    FuEnsemble,
    Generate,
    GenerateCodeBlock,
    MdEnsemble,
    Rephrase,
    Review,
    Revise,
    Test,
)
from examples.ags.w_action_node.utils import extract_test_cases_from_jsonl, get_hotpotqa
from metagpt.llm import LLM


class Graph:
    def __init__(self, name: str, llm: LLM) -> None:
        self.name = name
        self.model = llm

    def __call__():
        NotImplementedError("Subclasses must implement __call__ method")

    def optimize(dataset: List):
        pass


class HumanEvalGraph(Graph):
    def __init__(self, name: str, llm: LLM, criteria: str, vote_count: int = 5) -> None:
        super().__init__(name, llm)
        self.generate = Generate(llm=llm)
        self.criteria = criteria  # TODO 自动构建图时，图的初始参数与图所使用的算子要求的外部参数相匹配
        self.generate_code_block = GenerateCodeBlock(llm=llm)
        self.review = Review(llm=llm, criteria=criteria)
        self.revise = Revise(llm=llm)
        self.rephrase = Rephrase(llm=llm)
        self.tester = Test(llm=llm)
        self.fuensemble = FuEnsemble(llm=llm)
        self.mdensemble = MdEnsemble(llm=llm, vote_count=vote_count)
        self.codeensemble = CodeEnsmble(llm=llm, vote_count=vote_count)

    async def __call__(self, problem: str, function_name: str, ensemble_count: int = 3):
        solution_list = []
        for _ in range(ensemble_count):
            solution = await self.generate_code_block(problem, function_name)
            solution = solution.get("code_solution")
            solution_list.append(solution)
        solution = await self.mdensemble("code", solution_list, problem)
        return solution

    async def alpha_codium(self, problem_id: str, problem: str, ensemble_count: int = 3, test_loop: int = 3):
        """
        Paper: Code Generation with AlphaCodium: From Prompt Engineering to Flow Engineering
        Link: https://arxiv.org/abs/2404.14963
        Flow: An incomplete version of alpha codium, implementing the basic process of rephrase -> code ensemble -> tes
        """
        test_cases = extract_test_cases_from_jsonl(problem_id)
        entry_point = get_human_eval_plus()[problem_id]["entry_point"]
        rephrase_problem = await self.rephrase(problem)  # 在rephrase 中拼接原始的问题描述
        code_solution_list = []
        solution_list = []

        for _ in range(ensemble_count):
            """对文字版本的Solution进行ensemble"""
            code_solution = await self.generate.code_solution_generate(problem, rephrase_problem)
            code_solution = code_solution.get("content")
            code_solution_list.append(code_solution)
        final_code_solution = await self.mdensemble(code_solution_list, problem)
        final_code_solution = final_code_solution.get("final_solution")
        thought = f"""Reflection on the problem:\n{rephrase_problem} \n\nPossible solution:\n{final_code_solution}"""

        for _ in range(ensemble_count):
            """对代码版本的Solution进行ensemble"""
            solution = await self.generate_code_block.rephrase_generate(problem, thought, function_name=entry_point)
            solution = solution.get("code_solution")
            solution_list.append(solution)
        solution = await self.codeensemble(solution_list, problem)
        solution = await self.tester(
            problem_id, problem, rephrase_problem, solution, test_cases, entry_point, test_loop
        )
        return solution

    async def review_revise_ensemble(self, problem: str, ensemble_count: int = 2, revise_round: int = 3):
        solution_list = []
        for _ in range(ensemble_count):
            solution = await self.single_solve(problem, revise_round)
            solution_list.append(solution)
        solution = await self.ensemble(solution_list, problem)
        return solution

    async def simple_ensemble(self, problem: str, ensemble_count: int = 3):
        solution_list = []
        for _ in range(ensemble_count):
            solution = await self.generate_code_block(problem)
            solution = solution.get("code_solution")
            solution_list.append(solution)
        solution = await self.fuensemble(solution_list, problem)
        return solution

    async def single_solve(self, problem: str, max_loop: int):
        solution = await self.generate_code_block(problem)
        solution = solution.get("code_solution")
        for _ in range(max_loop):
            review_feedback = await self.review(problem, solution)
            if review_feedback["review_result"]:
                break
            solution = await self.revise(problem, solution, review_feedback["feedback"])
            solution = solution.get("revised_solution")
        return solution


class Gsm8kGraph(Graph):
    def __init__(self, name: str, llm: LLM, criteria: str, vote_count: int = 5) -> None:
        super().__init__(name, llm)
        self.criteria = criteria
        self.generate = Generate(llm=llm)
        self.rephrase = Rephrase(llm=llm)
        self.fuensemble = FuEnsemble(llm=llm)
        self.mdensemble = MdEnsemble(llm=llm, vote_count=vote_count)
        self.review = Review(llm=llm, criteria=criteria)
        self.revise = Revise(llm=llm)
        self.format = Format(llm=llm)

    async def __call__(self, problem: str):
        rephrased_problem = await self.rephrase.math_rephrase(problem)
        solution = await self.generate.math_generate(rephrased_problem)
        formatted_solution = await self.format.math_answer_format(solution["solution"])
        return formatted_solution

    async def baseline(self, problem: str):
        solution = await self.generate(problem)
        formatted_solution = await self.format.math_answer_format(solution["solution"])
        return formatted_solution

    async def simple_ensemble(self, problem: str, ensemble_count: int = 3):
        rephrased_problem = await self.rephrase.math_rephrase(problem)
        solution_list = []
        answer_list = []

        for _ in range(ensemble_count):
            solution = await self.generate.math_generate(rephrased_problem)
            solution = solution.get("solution")
            answer = await self.format.math_answer_format(solution)
            solution_list.append(solution)
            answer_list.append(answer)

        if len(set(answer.get("solution") for answer in answer_list)) == 1:
            formatted_solution = answer_list[0]
        else:
            # TODO 我个人感觉针对数学这种情景，使用self consistency 的ensemble方法可能会更好
            solution = await self.mdensemble("math", solution_list, problem)
            formatted_solution = await self.format.math_answer_format(solution["final_solution"])

        return formatted_solution

    async def single_solve(self, problem: str, max_loop: int = 3):
        rephrased_problem = await self.rephrase.math_rephrase(problem)
        solution = await self.generate.math_generate(rephrased_problem)
        for _ in range(max_loop):
            review_feedback = await self.review(rephrased_problem, solution["solution"])
            if review_feedback["review_result"]:
                break
            solution = await self.revise(rephrased_problem, solution["solution"], review_feedback["feedback"])
            solution = solution.get("revised_solution")
        formatted_solution = await self.format.math_answer_format(solution)
        return formatted_solution

    async def cot_ensemble(self, problem: str, ensemble_count: int = 1):
        solution_list = []
        for _ in range(ensemble_count):
            core = await self.rephrase.math_core(problem)
            extract = await self.rephrase.math_extract(problem)
            formatted_problem = (
                f"### Problem\n{problem}\n### Problem-Solving Info\n{extract}\n### Core Question\n{core}\n"
            )
            solution = await self.generate.math_generate(formatted_problem)  # 等待 generate 方法完成
            solution0 = solution.get("solution")
            solution_list.append(solution0)
        solution = await self.fuensemble(solution_list, problem)
        solution0 = solution["solution"]
        formatted_solution = await self.format.math_answer_format(solution)
        return formatted_solution

    async def cot(self, problem: str):
        core = await self.rephrase.math_core(problem)
        extract = await self.rephrase.math_extract(problem)
        formatted_problem = f"### Problem\n{problem}\n### Problem-Solving Info\n{extract}\n### Core Question\n{core}\n"
        solution = await self.generate.math_generate(formatted_problem)  # 等待 generate 方法完成
        solution.get("solution")
        formatted_solution = await self.format.math_answer_format(solution)

        return formatted_solution


class HotpotQAGraph(Graph):
    def __init__(self, name: str, llm: LLM, criteria: str, HOTPOTQA_PATH: str) -> None:
        super().__init__(name, llm)
        self.generate = Generate(llm=llm)
        self.format = Format(llm=llm)
        self.review = Review(llm=llm, criteria=criteria)
        self.revise = Revise(llm=llm)
        self.hotpotqa_path = HOTPOTQA_PATH

    async def __call__(self, id: str, max_loop: int = 1):
        dp = get_hotpotqa(self.hotpotqa_path)[id]
        paragraphs = [item[1] for item in dp["context"] if isinstance(item[1], list)]
        context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)

        answer_result = await self.generate.context_solution_generate(dp["question"], context_str)
        answer_result = answer_result.get("solution")

        for _ in range(max_loop):
            review_result = await self.review(dp["question"], answer_result)
            if review_result["review_result"]:
                break
            answer_result = await self.revise(dp["question"], answer_result, review_result["feedback"])
            answer_result = answer_result.get("revised_solution")

        answer_formated = await self.format(dp["question"], answer_result)

        sample_dict = dict(task_id=id, answer=answer_formated.get("solution"))
        return sample_dict
