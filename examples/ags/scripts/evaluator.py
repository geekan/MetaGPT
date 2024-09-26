# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : evaluate for different dataset

import asyncio
import json
import multiprocessing
import re
from math import isclose
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union

import aiofiles
import numpy as np
import pandas as pd
import regex
from scipy.optimize import linear_sum_assignment
from sympy import N, simplify
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import parse_expr
from tqdm.asyncio import tqdm_asyncio

from examples.ags.benchmark.gsm8k import optimize_gsm8k_evaluation
from examples.ags.benchmark.math import optimize_math_evaluation
from examples.ags.benchmark.humaneval import optimize_humaneval_evaluation
from examples.ags.benchmark.hotpotqa import optimize_hotpotqa_evaluation
from examples.ags.benchmark.mbpp import optimize_mbpp_evaluation
from examples.ags.benchmark.drop import optimize_drop_evaluation

DatasetType = Literal["HumanEval", "MBPP", "Gsm8K", "MATH", "HotpotQA", "DROP"]


class Evaluator:
    """
    在这里完成对不同数据集的评估
    """

    def __init__(self, eval_path: str):
        self.eval_path = eval_path

    def graph_evaluate(self, dataset: DatasetType, graph, params: dict, path, is_test=False):
        """
        Evaluates on validation dataset.
        """
        if dataset == "Gsm8K":
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

    # def graph_evaluate(self, dataset: DatasetType, graph, params: dict, path):
    #     """
    #     dataset: dataset type
    #     graph: graph class
    #     params: params for graph
    #     path: path to save results
    #     """
    #     if dataset == "Gsm8K":
    #         return self._gsm8k_eval(graph, params, path, test=False)
    #     elif dataset == "MATH":
    #         return self._math_eval(graph, params, path, test=False)
    #     elif dataset == "HumanEval":
    #         return self._humaneval_eval(graph, params, path, test=False)
    #     elif dataset == "HotpotQA":
    #         return self._hotpotqa_eval(graph, params, path, test=False)
    #     elif dataset == "MBPP":
    #         return self._mbpp_eval(graph, params, path, test=False)
    #     elif dataset == "DROP":
    #         return self._drop_eval(graph, params, path, test=False)

    # def test_evaluate(self, dataset: DatasetType, graph, params: dict, path):
    #     """
    #     Evaluates on test dataset.
    #     """
    #     if dataset == "Gsm8K":
    #         return self._gsm8k_eval(graph, params, path, test=True)
    #     elif dataset == "MATH":
    #         return self._math_eval(graph, params, path, test=True)
    #     elif dataset == "HumanEval":
    #         return self._humaneval_eval(graph, params, path, test=True)
    #     elif dataset == "HotpotQA":
    #         return self._hotpotqa_eval(graph, params, path, test=True)
    #     elif dataset == "MBPP":
    #         return self._mbpp_eval(graph, params, path, test=True)
    #     elif dataset == "DROP":
    #         return self._drop_eval(graph, params, path, test=True)
    #     pass

    async def _gsm8k_eval(self, graph_class, params, path, test=False):
        """
        评估GSM8K数据集。
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="Gsm8K", llm_config=llm_config, dataset=dataset)

        if test:
            data_path = "examples/ags/scripts/data/gsm8k_test.jsonl"  # 替换为您的JSONL文件路径
            va_list = [0]
        else:
            data_path = "examples/ags/scripts/data/gsm8k_validation.jsonl"  # 替换为您的JSONL文件路径
            va_list = [155, 230, 137, 225, 96, 50, 130, 26, 79, 259, 131, 1, 242, 247, 191, 94, 185, 38, 104, 64,
                       68, 92, 118, 31, 107, 42, 141, 125, 18, 100, 135, 236, 145, 11, 217, 65, 170, 210, 82, 162,
                       235, 234, 186, 182, 190, 180, 189, 152, 181, 151, 187, 150, 183, 149, 147, 179, 188, 148,
                       184, 175, 178, 177, 160, 161, 158, 163, 164, 157, 156, 165, 166, 192, 167, 168, 154, 169,
                       171, 172, 153, 173, 174, 159, 176, 0, 202, 193, 194, 229, 231, 232, 233, 237, 238, 239, 240,
                       241, 243, 244, 245, 246]

        graph = await load_graph()
        
        avg_score, avg_cost, total_cost = await optimize_gsm8k_evaluation(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost

    async def _math_eval(self, graph_class, params, path, test=False):
        """
        评估MATH数据集。
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="MATH", llm_config=llm_config, dataset=dataset)
        
        if test:
            data_path = "examples/ags/data/math_test.jsonl"
        else:
            data_path = "examples/ags/data/math_validate.jsonl"

        graph = await load_graph()
        
        score, cost = await optimize_math_evaluation(graph, data_path, path)
        
        return score, cost

    async def _humaneval_eval(self, graph_class, params, path, test=False):
        """
        评估HumanEval数据集。
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="HumanEval", llm_config=llm_config, dataset=dataset)

        if test:
            data_path = "examples/ags/data/human-eval_test.jsonl"  # 替换为您的JSONL文件路径
            va_list = None
        else:
            data_path = "examples/ags/data/human-eval_validate.jsonl"  # 替换为您的JSONL文件路径
            va_list = [19, 21, 22, 23, 24, 25, 17, 26, 27, 28, 29, 30, 31, 18, 0, 1, 15, 14, 13, 12, 11, 10, 8, 7, 6, 5, 4, 3, 2, 32]

        graph = await load_graph()
        
        avg_score, avg_cost, total_cost = await optimize_humaneval_evaluation(graph, data_path, path, va_list)
        
        return avg_score, avg_cost, total_cost

    async def _hotpotqa_eval(self, graph_class, params, path, test=False):
        """
        评估HotpotQA数据集。
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="HotpotQA", llm_config=llm_config, dataset=dataset)
        
        if test:
            data_path = "examples/ags/data/hotpotqa_test.jsonl"
        else:
            data_path = "examples/ags/data/hotpotqa_validate.jsonl"

        graph = await load_graph()
        
        score, cost = await optimize_hotpotqa_evaluation(graph, data_path, path)
        
        return score, cost

    async def _mbpp_eval(self, graph_class, params, path, test=False):
        """
        评估MBPP数据集。
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="MBPP", llm_config=llm_config, dataset=dataset)
        
        if test:
            data_path = "examples/ags/data/mbpp_test.jsonl"
        else:
            data_path = "examples/ags/data/mbpp_validate.jsonl"

        graph = await load_graph()
        
        score, cost = await optimize_mbpp_evaluation(graph, data_path, path)
        
        return score, cost

    async def _drop_eval(self, graph_class, params, path, test=False):
        """
        评估DROP数据集。
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="DROP", llm_config=llm_config, dataset=dataset)
        
        if test:
            data_path = "examples/ags/data/drop_test.json"
        else:
            data_path = "examples/ags/data/drop_validate.json"

        graph = await load_graph()
        
        score, cost = await optimize_drop_evaluation(graph, data_path, path)
        
        return score, cost