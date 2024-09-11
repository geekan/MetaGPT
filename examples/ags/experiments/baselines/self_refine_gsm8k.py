from examples.ags.scripts.operator import Operator
from examples.ags.scripts.graph import SolveGraph
from examples.ags.benchmark.gsm8k import gsm8k_evaluation
from metagpt.actions.action_node import ActionNode 
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
from pydantic import BaseModel, Field
from typing import Dict, Any

GSM8K_PROMPT_GPT = """
{question}\nPlease reason step by step, and put your final answer in the end. Wrap content using xml tags.
"""

GSM8K_PROMPT_DS = """
{question}\nPlease reason step by step, and put your final answer within \\boxed{{}}.
"""

REVIEW_PROMPT = """
For the question described as {question},
please review the following solution: {solution}, and criticize on where might be wrong. You should provide a review result in boolean format.
If you believe the solution is capable of resolving the issue, return True; otherwise, return False, and include your feedback.
"""

REVISE_PROMPT = """
For the question described as {question}, \nand an error solution: {solution}, \nwith the feedback: {feedback},
Given the previous solution and feedback, carefully refine the solution to solve the question and ensure it aligns with the original format.
"""

class GenerateOp(BaseModel):
    solution: str = Field(default="", description="solution for the problem")

class ReviewOp(BaseModel):
    review_result: bool = Field(
        default=False,
        description="The Review Result (Bool). If you think this solution looks good for you, return 'true'; If not, return 'false'",
    )
    feedback: str = Field(
        default="",
        description="Your FeedBack for this problem based on the criteria. If the review result is true, you can put it 'nothing here'.",
    )


class ReviseOp(BaseModel):
    solution: str = Field(default="", description="Based on the feedback, revised solution for this problem")


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
    
class Review(Operator):
    def __init__(self, llm: LLM, name: str = "Review"):
        super().__init__(name, llm)

    async def __call__(self, problem, solution, mode: str = None):
        prompt = REVIEW_PROMPT.format(question=problem, solution=solution)
        fill_kwargs = {"context": prompt, "llm": self.llm}
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(ReviewOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

class Revise(Operator):
    def __init__(self, name: str = "Revise", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, problem, solution, feedback, mode: str = None):
        prompt = REVISE_PROMPT.format(question=problem, solution=solution, feedback=feedback)
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

    async def __call__(self, problem):
        solution = await self.cot_generate(problem, mode="context_fill")
        for i in range(5):
            review = await self.review(problem, solution)
            if review["review_result"]:
                break
            solution = await self.revise(problem, solution, review["feedback"])
        return solution, self.llm.cost_manager.total_cost

if __name__ == "__main__":
    async def main():
        llm_config = ModelsConfig.default().get("deepseek-coder")
        # llm_config = ModelsConfig.default().get("gpt-4o-mini")
        # llm_config = ModelsConfig.default().get("gpt-35-turbo-1106")
        graph = SelfRefineGraph(name="self-refine", llm_config=llm_config, dataset="Gsm8K")
        file_path = "examples/ags/data/gsm8k.jsonl"
        samples = 10
        path = "examples/ags/data/baselines/general"
        score, cost = await gsm8k_evaluation(graph, file_path, samples, path)
        return score, cost

    import asyncio
    asyncio.run(main())
