from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.math import math_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Tuple
from collections import Counter

import random

GENERATE_COT_PROMPT = """
{question}\nPlease reason step by step. At the end, provide the final answer in the format "\\boxed{{<number>}}", where <number> is a math answer(an expression or number), without any additional information or explanation.
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="solution for the problem")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, mode: str = None):
        prompt = GENERATE_COT_PROMPT.format(question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response


MD_ENSEMBLE_PROMPT = """
You are given a problem:
{question}

Here is a list of possible solutions to the problem:
{solutions}

Using the inputs above, your goal is to choose the best solution to the problem.
The main consideration is that the solution can fully solve the problem in a correct and robust manner.
Provide your final decision by writing the chosen solution letter.

Please follow the required format in your response.
"""

class MdEnsembleOp(BaseModel):
    thought: str = Field(
        default="",
        description="Step-by-step analysis of the solutions to determine the best one.",
    )
    solution_letter: str = Field(default="", description="The letter of the chosen best solution (only one letter).")


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

    async def __call__(self, solutions: List[str], problem: str, mode: str = None):
        print(f"solution count: {len(solutions)}")
        all_responses = []

        for _ in range(self.vote_count):
            shuffled_solutions, answer_mapping = self.shuffle_answers(solutions)

            solution_text = ""
            for index, solution in enumerate(shuffled_solutions):
                solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

            prompt = MD_ENSEMBLE_PROMPT.format(solutions=solution_text, question=problem)
            fill_kwargs = {"context": prompt, "llm": self.llm}
            if mode:
                fill_kwargs["mode"] = mode
            node = await ActionNode.from_pydantic(MdEnsembleOp).fill(**fill_kwargs)
            response = node.instruct_content.model_dump()

            answer = response.get("solution_letter", "")
            answer = answer.strip().upper()

            if answer in answer_mapping:
                original_index = answer_mapping[answer]
                all_responses.append(original_index)

        most_frequent_index = Counter(all_responses).most_common(1)[0][0]
        final_answer = solutions[most_frequent_index]
        return {"solution": final_answer}  

class MedPromptGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str, vote_count: int = 3):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = CoTGenerate(llm=self.llm)
        self.md_ensemble = MdEnsemble(llm=self.llm, vote_count=vote_count)

    async def __call__(self, problem):
        solutions = []
        for i in range(2):
            solution = await self.cot_generate(problem, mode="context_fill")
            solutions.append(solution["solution"])
        solution = await self.md_ensemble(solutions, problem, mode="context_fill")
        return solution, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        graph = MedPromptGraph(name="MedPrompt", llm_config=llm_config, dataset="Gsm8K", vote_count=2)
        file_path = "examples/ags/data/math_test.jsonl"
        # samples = None
        samples = 0
        path = "examples/ags/data/baselines/general/math"
        score = await math_evaluation(graph, file_path, samples, path,test=True)
        return score

    import asyncio
    asyncio.run(main())