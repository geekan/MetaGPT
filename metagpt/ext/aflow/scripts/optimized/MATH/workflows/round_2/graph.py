from typing import Literal
import metagpt.ext.aflow.scripts.optimized.MATH.workflows.template.operator as operator
import metagpt.ext.aflow.scripts.optimized.MATH.workflows.round_2.prompt as prompt_custom
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager

DatasetType = Literal["HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP"]

class Workflow:
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
        self.custom = operator.Custom(self.llm)
        self.sc_ensemble = operator.ScEnsemble(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the workflow
        """
        initial_solution = await self.custom(input=problem, instruction=prompt_custom.INITIAL_SOLUTION_PROMPT)
        revised_solution = await self.custom(input=problem + f"\nInitial solution: {initial_solution['response']}", instruction=prompt_custom.REVISE_SOLUTION_PROMPT)
        final_solution = await self.sc_ensemble(solutions=[initial_solution['response'], revised_solution['response']], problem=problem)
        return final_solution['response'], self.llm.cost_manager.total_cost
