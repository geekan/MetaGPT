from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.hotpotqa import hotpotqa_evaluation
from examples.ags.scripts.operator_an import GenerateOp
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Tuple
from collections import Counter

import random

HOTPOTQA_PROMPT = """
Solve a question answering task by having a Thought, then finish with your answer. Thought can reason about the current situation. Return the answer in few words. You will be given context that you should use to help you answer the question.
Relevant Context: {context} 
Question: {question}
Thought: {thought}
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="The thought or answer to the problem")

class CoTGenerate(Operator):
    def __init__(self, llm: LLM, name: str = "Generate"):
        super().__init__(name, llm)

    async def __call__(self, question: str, context: str, mode: str = None) -> Tuple[str, str]:
        thought = ""
        prompt = HOTPOTQA_PROMPT.format(question=question, context=context, thought=thought)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()

        thought = response["solution"]

        prompt = HOTPOTQA_PROMPT.format(question=question, context=context, thought=thought)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(GenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response["solution"]

SC_ENSEMBLE_PROMPT = """
Given the question descripted as follows: {question}
And the relevant context is provided as follows: {context}
some solutions to the question are generated as follows:
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

    async def __call__(self, solutions: List[str], problem: str, context: str, mode: str = None):
        answer_mapping = {}
        solution_text = ""
        for index, solution in enumerate(solutions):
            answer_mapping[chr(65 + index)] = index
            solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

        prompt = SC_ENSEMBLE_PROMPT.format(solutions=solution_text, question=problem, context = context)
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

    async def __call__(self, problem, context):
        solutions = []
        for i in range(5):
            solution = await self.cot_generate(problem, context, mode="context_fill")
            solutions.append(solution)
        solution = await self.sc_ensemble(solutions, problem, context, mode="context_fill")
        return solution, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        # llm_config = ModelsConfig.default().get("deepseek-coder")
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        graph = SelfConsistencyGraph(name="SelfConsistency", llm_config=llm_config, dataset="HotpotQA")
        file_path = "examples/ags/data/hotpotqa.jsonl"
        samples = 10
        path = "examples/ags/data/baselines/general/hotpotqa"
        score = await hotpotqa_evaluation(graph, file_path, samples, path, test=False)
        return score

    import asyncio
    asyncio.run(main())