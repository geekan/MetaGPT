from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.gsm8k import gsm8k_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Tuple
from collections import Counter

import random

GSM8K_PROMPT_GPT = """
{question}\nPlease reason step by step, and to ensure accuracy, provide the correct answer in the final, without any additional text.
"""

GSM8K_PROMPT_DS = """
{question}\nPlease reason step by step, and put your final answer within \\boxed{{}}.
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="solution for the problem")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, problem, mode: str = None):
        prompt = GSM8K_PROMPT_GPT.format(question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

SC_ENSEMBLE_PROMPT = """
Given the question descripted as follows: {question}
some solutions are generated to solve the question as follows:
{solutions}

Evaluate these solutions and select the most consistent solution based on majority consensus.
Give your answer with a single id of solution (without anything else).
"""

class ScEnsembleOp(BaseModel):
    solution_letter: str = Field(default="", description="The letter of most consistent solution.")


class ScEnsemble(Operator):
    """
    Paper: Self-Consistency Improves Chain of Thought Reasoning in Language Models
    Link: https://arxiv.org/abs/2203.11171
    Paper: Universal Self-Consistency for Large Language Model Generation
    Link: https://arxiv.org/abs/2311.17311
    """

    def __init__(self, name: str = "ScEnsemble", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, solutions: List[str], problem: str, mode: str = None):
        answer_mapping = {}
        solution_text = ""
        for index, solution in enumerate(solutions):
            answer_mapping[chr(65 + index)] = index
            solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

        prompt = SC_ENSEMBLE_PROMPT.format(solutions=solution_text, question=problem)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(ScEnsembleOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()

        answer = response.get("solution_letter", "")
        answer = answer.strip().upper()

        return {"solution": solutions[answer_mapping[answer]]}


class SelfConsistencyGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = CoTGenerate(self.llm)
        self.sc_ensemble = ScEnsemble(self.llm)

    async def __call__(self, problem):
        solutions = []
        for i in range(2):
            solution = await self.cot_generate(problem, mode="context_fill")
            solutions.append(solution["solution"])
        solution = await self.sc_ensemble(solutions, problem, mode="context_fill")
        return solution, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("deepseek-coder")
        # llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        graph = SelfConsistencyGraph(name="SelfConsistency", llm_config=llm_config, dataset="Gsm8K")
        file_path = "examples/ags/data/gsm8k.jsonl"
        samples = 1
        path = "examples/ags/data/baselines/general"
        score, cost = await gsm8k_evaluation(graph, file_path, samples, path, test=False)
        return score, cost

    import asyncio
    asyncio.run(main())