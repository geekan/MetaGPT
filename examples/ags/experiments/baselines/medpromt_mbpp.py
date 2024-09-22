from examples.ags.benchmark.mbpp import mbpp_evaluation
from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Tuple
from collections import Counter
import random

MBPP_PROMPT_COT = """
{question}\nPlease provide a step-by-step explanation in text, followed by your Python function, ensure the output code is self-contained, meaning it should have the correct function name and return statement, without any additional text."""


MD_ENSEMBLE_PROMPT = """
Given the question described as follows: {question}
Several solutions have been generated to address the given question. They are as follows:
{solutions}

Carefully evaluate these solutions and identify the solution that is more capable of solving the problem compared to other solutions, as this is crucial for problem-solving.

In the "thought" field, provide a detailed explanation of your thought process. In the "solution_letter" field, output only the single letter ID (A, B, C, etc.) corresponding to the solution. Do not include any additional text or explanation in the "solution_letter" field.
"""


class GenerateOp(BaseModel):
    solution: str = Field(default="", description="Python Solution For This Question.")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, function_name, mode: str = None):
        prompt = MBPP_PROMPT_COT.format(question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm, "function_name": function_name}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

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

    def __init__(self, llm: LLM, name: str = "MdEnsemble", vote_count: int = 5):
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

            answer = response.get("solution_letter", "A")
            answer = answer.strip().upper()

            if answer in answer_mapping:
                original_index = answer_mapping[answer]
                all_responses.append(original_index)

        most_frequent_index = Counter(all_responses).most_common(1)[0][0]
        final_answer = solutions[most_frequent_index]
        return {"solution": final_answer}  

class MedPromptGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str, vote_count: int = 5):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = CoTGenerate(self.llm)
        self.md_ensemble = MdEnsemble(self.llm, vote_count=vote_count)

    async def __call__(self, problem, function_name):
        solutions = []
        for i in range(3):
            solution = await self.cot_generate(problem, function_name, mode="code_fill")
            solutions.append(solution["solution"])
        solution = await self.md_ensemble(solutions, problem, mode="context_fill")
        return solution["solution"], self.llm.cost_manager.total_cost


if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("deepseek-chat")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo")
        graph = MedPromptGraph(name="MedPrompt", llm_config=llm_config, dataset="MBPP")
        file_path = "examples/ags/data/mbpp-new-new.jsonl"
        samples = 86 # 86/341
        path = "examples/ags/data/baselines/general/mbpp"
        score = await mbpp_evaluation(graph, file_path, samples, path, test=True)
        return score

    import asyncio
    asyncio.run(main())

