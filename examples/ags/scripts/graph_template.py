from typing import Literal

from evalplus.data import get_human_eval_plus

# from examples.ags.scripts.optimized.Gsm8K.operators.template.operator import *
from examples.ags.scripts.operator import *
from examples.ags.scripts.utils import extract_test_cases_from_jsonl
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager

DatasetType = Literal["HumanEval", "MBPP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]


# Contextual Generate Graph
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
        self.rephrase = Rephrase(self.llm)
        self.contextual_generate = ContextualGenerate(self.llm)
        self.format = Format(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the graph based on the generate operator, you can modify it to fit operators you want to use.
        For Example, for Custom Operator, you can add self.custom = Custom(self.llm) and call it in the __call__ method
        """
        # The following is the most basic invocation, attempting to introduce your newly modified 'Operator' to test its effect.The `format` method must be placed at the final layer
        rephrase_problem = await self.rephrase(problem)
        solution = await self.contextual_generate(problem, rephrase_problem)
        format_solution = await self.format(problem=problem, solution=solution["response"])
        return format_solution, self.llm.cost_manager.total_cost


# CodeGenerate Graph
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
        self.code_generate = CodeGenerate(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the graph based on the generate operator, you can modify it to fit operators you want to use.
        For Example, for Custom Operator, you can add self.custom = Custom(self.llm) and call it in the __call__ method
        """
        # The following is the most basic invocation, attempting to introduce your newly modified 'Operator' to test its effect.The `format` method must be placed at the final layer
        solution = await self.code_generate(problem)
        return solution, self.llm.cost_manager.total_cost


# Contextual CodeGenerate Graph
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
        self.rephrase = Rephrase(self.llm)
        self.code_contextual_generate = CodeContextualGenerate(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the graph based on the generate operator, you can modify it to fit operators you want to use.
        For Example, for Custom Operator, you can add self.custom = Custom(self.llm) and call it in the __call__ method
        """
        # The following is the most basic invocation, attempting to introduce your newly modified 'Operator' to test its effect.The `format` method must be placed at the final layer
        rephrase_problem = await self.rephrase(problem)
        solution = await self.code_contextual_generate(problem, rephrase_problem)
        return solution, self.llm.cost_manager.total_cost


# Test Graph
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
        self.generate = Generate(self.llm)
        self.test = Test(self.llm)

    async def __call__(self, problem_id: str, problem: str, test_loop: int = 3, rephrase_problem: str = "None"):
        """
        Implementation of the graph based on the generate operator, you can modify it to fit operators you want to use.
        For Example, for Custom Operator, you can add self.custom = Custom(self.llm) and call it in the __call__ method
        """
        # The following is the most basic invocation, attempting to introduce your newly modified 'Operator' to test its effect.The `format` method must be placed at the final layer
        test_cases = extract_test_cases_from_jsonl(problem_id)
        entry_point = get_human_eval_plus()[problem_id]["entry_point"]
        solution = await self.generate(problem)
        solution = await self.test(problem_id, problem, rephrase_problem, solution, test_cases, entry_point, test_loop)
        return solution, self.llm.cost_manager.total_cost


class SolveGraph:
    def __init__(self, name: str, llm_config, dataset: DatasetType, vote_count: int = 5) -> None:
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.generate = Generate(self.llm)
        self.med_ensemble = MdEnsemble(self.llm)
        self.vote_count = vote_count

    async def __call__(self, problem: str):
        solutions = []
        for i in range(self.vote_count):
            solution = await self.generate(problem)
            solutions.append(solution)
        solution = await self.med_ensemble(solutions)

        return solution, self.llm.cost_manager.total_cost


class SolveGraph:
    def __init__(self, name: str, llm_config, dataset: DatasetType, vote_count: int = 5) -> None:
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.generate = Generate(self.llm)
        self.fu_ensemble = FuEnsemble(self.llm)
        self.vote_count = vote_count

    async def __call__(self, problem: str):
        solutions = []
        for i in range(self.vote_count):
            solution = await self.generate(problem)
            solutions.append(solution)
        solution = await self.fu_ensemble(solutions)

        return solution, self.llm.cost_manager.total_cost


class SolveGraph:
    def __init__(self, name: str, llm_config, dataset: DatasetType, vote_count: int = 5) -> None:
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.generate = Generate(self.llm)
        self.sc_ensemble = ScEnsemble(self.llm)
        self.vote_count = vote_count

    async def __call__(self, problem: str):
        solutions = []
        for i in range(self.vote_count):
            solution = await self.generate(problem)
            solutions.append(solution)
        solution = await self.sc_ensemble(solutions)

        return solution, self.llm.cost_manager.total_cost


class SolveGraph:
    def __init__(self, name: str, llm_config, dataset: DatasetType, vote_count: int = 5) -> None:
        self.vote_count = vote_count
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.llm.cost_manager = CostManager()
        self.generate = CodeGenerate(self.llm)
        self.code_ensemble = CodeEnsemble(self.llm)

    async def __call__(self, problem: str):
        solutions = []
        for i in range(self.vote_count):
            solution = await self.generate(problem)
            solutions.append(solution)
        solution = await self.code_ensemble(solutions)

        return solution, self.llm.cost_manager.total_cost
