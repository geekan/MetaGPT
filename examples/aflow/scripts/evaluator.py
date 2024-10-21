# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : Evaluation for different datasets

from typing import Literal, Tuple, Optional, Dict
import asyncio

from examples.aflow.benchmark.benchmark import BaseBenchmark
from examples.aflow.benchmark.gsm8k import GSM8KBenchmark
from examples.aflow.benchmark.math import MATHBenchmark
from examples.aflow.benchmark.humaneval import HumanEvalBenchmark
from examples.aflow.benchmark.hotpotqa import HotpotQABenchmark
from examples.aflow.benchmark.mbpp import MBPPBenchmark
from examples.aflow.benchmark.drop import DROPBenchmark

# If you want to customize tasks, add task types here and provide evaluation functions, just like the ones given above
DatasetType = Literal["HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP"]

class Evaluator:
    """
    Complete the evaluation for different datasets here
    """

    def __init__(self, eval_path: str):
        self.eval_path = eval_path
        self.dataset_configs: Dict[DatasetType, BaseBenchmark] = {
            "GSM8K": GSM8KBenchmark,
            "MATH": MATHBenchmark,
            "HumanEval": HumanEvalBenchmark,
            "HotpotQA": HotpotQABenchmark,
            "MBPP": MBPPBenchmark,
            "DROP": DROPBenchmark,
        }

    async def graph_evaluate(self, dataset: DatasetType, graph, params: dict, path: str, is_test: bool = False) -> Tuple[float, float, float]:
        if dataset not in self.dataset_configs:
            raise ValueError(f"Unsupported dataset: {dataset}")

        data_path = self._get_data_path(dataset, is_test)
        benchmark_class = self.dataset_configs[dataset]
        benchmark = benchmark_class(dataset, data_path, path)

        # Use params to configure the graph and benchmark
        configured_graph = await self._configure_graph(graph, params)

        va_list = [1,2,3]  # Use va_list from params, or use default value if not provided
        return await benchmark.run_evaluation(configured_graph, va_list)

    async def _configure_graph(self, graph, params: dict):
        # Here you can configure the graph based on params
        # For example: set LLM configuration, dataset configuration, etc.
        dataset_config = params.get("dataset", {})
        llm_config = params.get("llm_config", {})
        return graph(name=self.dataset_configs[dataset]["name"], llm_config=llm_config, dataset=dataset_config)

    def _get_data_path(self, dataset: DatasetType, test: bool) -> str:
        base_path = f"examples/aflow/data/{dataset.lower()}"
        return f"{base_path}_test.jsonl" if test else f"{base_path}_validate.jsonl"

# Alias methods for backward compatibility
for dataset in ["gsm8k", "math", "humaneval", "mbpp", "hotpotqa", "drop"]:
    setattr(Evaluator, f"_{dataset}_eval", lambda self, *args, dataset=dataset.upper(), **kwargs: self.graph_evaluate(dataset, *args, **kwargs))
