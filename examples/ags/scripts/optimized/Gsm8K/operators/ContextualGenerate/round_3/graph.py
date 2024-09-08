from typing import Literal

from examples.ags.scripts.optimized.Gsm8K.operators.ContextualGenerate.round_3.operator import *
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
        self.contextual_generate = ContextualGenerate(self.llm)
        self.format = Format(self.llm)
        self.custom = Custom(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the graph based on the generate operator, you can modify it to fit operators you want to use.
        For Example, for Custom Operator, you can add self.custom = Custom(self.llm) and call it in the __call__ method
        """
        # The following is the most basic invocation, attempting to introduce your newly modified 'Operator' to test its effect.The `format` method must be placed at the final layer
        information = await self.custom(
            input=problem, instruction="Give the key information of the topic in one sentence"
        )
        solution = await self.contextual_generate(problem, information)
        format_solution = await self.format(problem=problem, solution=solution["response"])
        return format_solution, self.llm.cost_manager.total_cost
