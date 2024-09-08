from typing import Literal

from examples.ags.scripts.optimized.Gsm8K.operators.Review.round_1.operator import *
from examples.ags.scripts.optimized.Gsm8K.operators.template.operator import (
    Custom,
    Format,
)
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager

DatasetType = Literal["HumanEval", "MBPP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]


class SolveGraph:
    def __init__(
        self,
        name: str,
        llm_config,
        dataset: DatasetType,
    ) -> None:
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.llm.cost_manager = CostManager()
        self.format = Format(self.llm)
        self.custom = Custom(self.llm)
        self.review = Review(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the graph based on the generate operator, you can modify it to fit operators you want to use.
        For Example, for Custom Operator, you can add self.custom = Custom(self.llm) and call it in the __call__ method
        """
        # The following is the most basic invocation, attempting to introduce your newly modified 'Operator' to test its effect.The `format` method must be placed at the final layer.

        solution = None
        for i in range(5):
            solution = await self.custom(input=problem, instruction="")
            review_result = await self.review(problem, solution["response"])
            if review_result["review_result"] == "True":
                break
            elif review_result["review_result"] == "False":
                continue
            else:
                break

        format_solution = await self.format(problem=problem, solution=solution["response"])
        return format_solution, self.llm.cost_manager.total_cost
