# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : Evaluation for different datasets

from typing import Literal, Tuple, Optional
import asyncio

from examples.aflow.benchmark.gsm8k import optimize_gsm8k_evaluation
from examples.aflow.benchmark.math import optimize_math_evaluation
from examples.aflow.benchmark.humaneval import optimize_humaneval_evaluation
from examples.aflow.benchmark.hotpotqa import optimize_hotpotqa_evaluation
from examples.aflow.benchmark.mbpp import optimize_mbpp_evaluation
from examples.aflow.benchmark.drop import optimize_drop_evaluation

# If you want to customize tasks, add task types here and provide evaluation functions, just like the ones given above
DatasetType = Literal["HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP"]

class Evaluator:
    """
    Complete the evaluation for different datasets here
    """

    def __init__(self, eval_path: str):
        self.eval_path = eval_path
        self.dataset_configs = {
            "GSM8K": {"name": "GSM8K", "eval_func": optimize_gsm8k_evaluation},
            "MATH": {"name": "MATH", "eval_func": optimize_math_evaluation},
            "HumanEval": {"name": "HumanEval", "eval_func": optimize_humaneval_evaluation},
            "HotpotQA": {"name": "HotpotQA", "eval_func": optimize_hotpotqa_evaluation},
            "MBPP": {"name": "MBPP", "eval_func": optimize_mbpp_evaluation},
            "DROP": {"name": "DROP", "eval_func": optimize_drop_evaluation},
        }

    def graph_evaluate(self, dataset: DatasetType, graph, params: dict, path, is_test=False):
        """
        Evaluates on validation dataset.
        """
        if dataset in self.dataset_configs:
            return self._generic_eval(dataset, graph, params, path, is_test)
        else:
            return None

    async def _generic_eval(self, dataset: DatasetType, graph_class, params: dict, path: str, test: bool = False) -> Tuple[float, float, float]:
        """
        Generic evaluation function for all datasets.
        """
        async def load_graph():
            dataset_config = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name=self.dataset_configs[dataset]["name"], llm_config=llm_config, dataset=dataset_config)

        data_path, va_list = self._get_data_path_and_va_list(dataset, test)
        graph = await load_graph()
        
        eval_func = self.dataset_configs[dataset]["eval_func"]
        avg_score, avg_cost, total_cost = await eval_func(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost

    def _get_data_path_and_va_list(self, dataset: DatasetType, test: bool) -> Tuple[str, Optional[list]]:
        """
        Get data path and validation list based on dataset and test flag.
        """
        base_path = f"examples/aflow/data/{dataset.lower()}"
        if test:
            return f"{base_path}_test.jsonl", None
        else:
            return f"{base_path}_validate.jsonl", [1, 2, 3]  # Replace with the actual filtered index list

# Alias methods for backward compatibility
for dataset in ["gsm8k", "math", "humaneval", "mbpp", "hotpotqa", "drop"]:
    setattr(Evaluator, f"_{dataset}_eval", lambda self, *args, dataset=dataset.upper(), **kwargs: self._generic_eval(dataset, *args, **kwargs))