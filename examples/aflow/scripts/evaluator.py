# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : Evaluation for different datasets

from typing import Literal

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

    def graph_evaluate(self, dataset: DatasetType, graph, params: dict, path, is_test=False):
        """
        Evaluates on validation dataset.
        """
        if dataset == "GSM8K":
            return self._gsm8k_eval(graph, params, path, is_test)
        elif dataset == "MATH":
            return self._math_eval(graph, params, path, is_test)
        elif dataset == "HumanEval":
            return self._humaneval_eval(graph, params, path, is_test)
        elif dataset == "HotpotQA":
            return self._hotpotqa_eval(graph, params, path, is_test)
        elif dataset == "MBPP":
            return self._mbpp_eval(graph, params, path, is_test)
        elif dataset == "DROP":
            return self._drop_eval(graph, params, path, is_test)
        else:
            return None

    async def _gsm8k_eval(self, graph_class, params, path, test=False):
        """
        Evaluate GSM8K dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="GSM8K", llm_config=llm_config, dataset=dataset)

        if test:
            data_path = "examples/aflow/data/gsm8k_test.jsonl"  # Replace with your JSONL file path
            va_list = None
        else:
            data_path = "examples/aflow/data/gsm8k_validate.jsonl"  # Replace with your JSONL file path
            va_list = [1,2,3] # Replace with the filtered index list

        graph = await load_graph()
        
        avg_score, avg_cost, total_cost = await optimize_gsm8k_evaluation(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost

    async def _math_eval(self, graph_class, params, path, test=False):
        """
        Evaluate MATH dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="MATH", llm_config=llm_config, dataset=dataset)
        
        if test:
            data_path = "examples/aflow/data/math_test.jsonl"
            va_list = None
        else:
            data_path = "examples/aflow/data/math_validate.jsonl"
            va_list = [1,2,3] # Replace with the filtered index list

        graph = await load_graph()
        
        avg_score, avg_cost, total_cost = await optimize_math_evaluation(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost

    async def _humaneval_eval(self, graph_class, params, path, test=False):
        """
        Evaluate HumanEval dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="HumanEval", llm_config=llm_config, dataset=dataset)

        if test:
            data_path = "examples/aflow/data/human-eval_test.jsonl"  # Replace with your JSONL file path
            va_list = None
        else:
            data_path = "examples/aflow/data/human-eval_validate.jsonl"  # Replace with your JSONL file path
            va_list = [1,2,3] # Replace with the filtered index list

        graph = await load_graph()
        
        avg_score, avg_cost, total_cost = await optimize_humaneval_evaluation(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost

    async def _mbpp_eval(self, graph_class, params, path, test=False):
        """
        Evaluate MBPP dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="MBPP", llm_config=llm_config, dataset=dataset)
        
        if test:
            data_path = "examples/aflow/data/mbpp_test.jsonl"
            va_list = None 
        else:
            data_path = "examples/aflow/data/mbpp_validate.jsonl"
            va_list = [1,2,3] # Replace with the filtered index list

        graph = await load_graph()
        
        avg_score, avg_cost, total_cost = await optimize_mbpp_evaluation(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost

    async def _hotpotqa_eval(self, graph_class, params, path, test=False):
        """
        Evaluate HotpotQA dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="HotpotQA", llm_config=llm_config, dataset=dataset)
        
        if test:
            data_path = "examples/aflow/data/hotpotqa_test.jsonl"
            va_list = None
        else:
            data_path = "examples/aflow/data/hotpotqa_validate.jsonl"
            va_list = [1,2,3] # Replace with the filtered index list

        graph = await load_graph()
        
        avg_score, avg_cost, total_cost = await optimize_hotpotqa_evaluation(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost
    

    async def _drop_eval(self, graph_class, params, path, test=False):
        """
        Evaluate DROP dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="DROP", llm_config=llm_config, dataset=dataset)
        
        if test:
            data_path = "examples/aflow/data/drop_test.jsonl"
            va_list = None
        else:
            data_path = "examples/aflow/data/drop_validate.jsonl"
            va_list = [1,2,3] # Replace with the filtered index list

        graph = await load_graph()
        
        avg_score, avg_cost, total_cost = await optimize_drop_evaluation(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost