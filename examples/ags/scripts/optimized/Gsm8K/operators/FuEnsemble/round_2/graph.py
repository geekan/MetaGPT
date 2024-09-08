from typing import Literal

from examples.ags.scripts.optimized.Gsm8K.operators.FuEnsemble.round_2.operator import *
from examples.ags.scripts.optimized.Gsm8K.operators.template.operator import (
    Custom,
    Format,
)
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager

DatasetType = Literal["HumanEval", "MBPP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]


class SolveGraph:
    def __init__(self, name: str, llm_config, dataset: DatasetType, vote_count: int = 5) -> None:
        self.name = name
        self.dataset = dataset
        self.vote_count = vote_count
        self.llm = create_llm_instance(llm_config)
        self.llm.cost_manager = CostManager()
        self.fu_ensemble = FuEnsemble(self.llm)
        self.format = Format(self.llm)
        self.custom = Custom(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the graph based on the generate operator, you can modify it to fit operators you want to use.
        For Example, for Custom Operator, you can add self.custom = Custom(self.llm) and call it in the __call__ method
        """
        # The following is the most basic invocation, attempting to introduce your newly modified 'Operator' to test its effect.The `format` method must be placed at the final layer
        solutions = []
        for i in range(self.vote_count):
            solution = await self.custom(problem, instruction="")
            solutions.append(solution)
        solution = await self.fu_ensemble(problem=problem, solutions=solutions)
        format_solution = await self.format(problem=problem, solution=solution["solution"])
        return format_solution, self.llm.cost_manager.total_cost
