from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.mbpp import mbpp_evaluation
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any

MBPP_PROMPT_COT = """
{question}\nPlease provide a step-by-step explanation in text, followed by your Python function, ensure the output code is self-contained, meaning it should have the correct function name and return statement, without any additional text."""


REVIEW_PROMPT = """
Given a problem and a thoughtful solution, your task is to using critical thinking (questioning) to review the solution's correctness and provide a review result in boolean format.

problem: {problem}
solution: {solution}

If you are more than 95 percent confident that the final answer is incorrect, please return False and give a feedback for the error. Otherwise, please return True and give a explanation for the correctness.
"""

REVISE_PROMPT = """
Given a problem and a thoughtful solution which is just reviewed as incorrect, your task is to revise the solution to solve the question and ensure the final code solution is wrapped with ```python```.

problem: {problem}
solution: {solution}
feedback: {feedback}

Ensure the output code is self-contained, meaning it should have the correct function name and return statement, without any additional text.
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="solution for the problem")

class ReviewOp(BaseModel):
    feedback: str = Field(
        default="",
        description="Your FeedBack for this problem based on the criteria. If the review result is true, you can put it 'nothing here'.",
    )
    review_result: bool = Field(
        default=False,
        description="The Review Result (Bool). If you think this solution looks good for you, return 'true'; If not, return 'false'",
    )

class ReviseOp(BaseModel):
    solution: str = Field(default="", description="Based on the feedback, revised solution for this problem")

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

    
class Review(Operator):
    def __init__(self, llm: LLM, name: str = "Review"):
        super().__init__(name, llm)

    async def __call__(self, problem, solution, mode: str = None):
        prompt = REVIEW_PROMPT.format(problem=problem, solution=solution)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(ReviewOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

class Revise(Operator):
    def __init__(self, llm: LLM, name: str = "Revise"):
        super().__init__(name, llm)

    async def __call__(self, problem, solution, feedback, mode: str = None):
        prompt = REVISE_PROMPT.format(problem=problem, solution=solution, feedback=feedback)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(ReviseOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response  

class SelfRefineGraph(SolveGraph):
    def __init__(self, name: str, llm_config, dataset: str):
        super().__init__(name, llm_config, dataset)
        self.cot_generate = CoTGenerate(self.llm)
        self.review = Review(self.llm)
        self.revise = Revise(self.llm)

    async def __call__(self, problem, function_name):
        solution = await self.cot_generate(problem, function_name, mode="code_fill")
        for i in range(3):
            review = await self.review(problem, solution, mode="context_fill")
            if review["review_result"]:
                break
            solution = await self.revise(problem, solution, review["feedback"], mode="code_fill")
        return solution["solution"], self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("gpt-4o-mini")
        graph = SelfRefineGraph(name="self-refine", llm_config=llm_config, dataset="MBPP")
        file_path = "examples/ags/data/mbpp-new-new.jsonl"
        samples = 86# 86/341
        path = "examples/ags/data/baselines/general/mbpp"
        score, cost = await mbpp_evaluation(graph, file_path, samples, path, test=True)
        print(f"per cost:{cost/341}")
        return score 

    import asyncio
    asyncio.run(main())
