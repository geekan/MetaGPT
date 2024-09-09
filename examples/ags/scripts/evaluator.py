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

from examples.ags.benchmark.gsm8k import gsm8k_evaluation
from examples.ags.benchmark.utils import generate_random_indices
from examples.ags.benchmark.math import math_evaluation
from examples.ags.benchmark.humaneval import humaneval_evaluation
from examples.ags.benchmark.mbpp import mbpp_evaluation
from examples.ags.benchmark.drop import drop_evaluation
from examples.ags.benchmark.hotpotqa import hotpotqa_evaluation

DatasetType = Literal["HumanEval", "MBPP", "Gsm8K", "MATH", "HotpotQA", "DROP"]


class Evaluator:
    """
    在这里完成对不同数据集的评估
    """

    def __init__(self, eval_path: str):
        self.eval_path = eval_path

    def validation_evaluate(self, dataset: DatasetType, graph, params: dict, path):
        """
        Evaluates on validation dataset.
        """
        if dataset == "Gsm8K":
            return self._gsm8k_eval(graph, params, path)
        elif dataset == "MATH":
            return self._math_eval(graph, params, path)
        elif dataset == "HumanEval":
            return self._humaneval_eval(graph, params, path)
        elif dataset == "HotpotQA":
            return self._hotpotqa_eval(graph, params, path)
        elif dataset == "MBPP":
            return self._mbpp_eval(graph, params, path)
        elif dataset == "DROP":
            return self._drop_eval(graph, params, path)

    def test_evaluate(self, dataset: DatasetType):
        """
        Evaluates on test dataset.
        """
        pass

    async def _gsm8k_eval(self, graph_class, params, path, samples: int = 50):
        """
        Evaluate on GSM8K dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="Gsm8K", llm_config=llm_config, dataset=dataset)

        graph = await load_graph()
        file_path = "examples/ags/data/gsm8k.jsonl"
        
        score = await gsm8k_evaluation(graph, file_path, samples, path)
        
        return score

    async def _math_eval(self, graph_class, params, path, samples: int = 200):
        """
        Evaluate on MATH dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="MATH", llm_config=llm_config, dataset=dataset)

        graph = await load_graph()
        file_path = "examples/ags/w_action_node/data/math.jsonl"  # 替换为实际的 MATH.jsonl 路径
        
        score = await math_evaluation(graph, file_path, samples, path)
        
        return score

    async def _humaneval_eval(self, graph_class, params, path, samples: int = 1):
        """
        Evaluate on HumanEval dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="HumanEval", llm_config=llm_config, dataset=dataset)

        graph = await load_graph()
        file_path = "examples/ags/scripts/data/human-eval-new.jsonl"
        
        score = await humaneval_evaluation(graph, file_path, samples, path)
        
        return score

    async def _hotpotqa_eval(self, graph_class, params, path, samples: int = 20):
        """
        Evaluate on HotpotQA dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="HotpotQA", llm_config=llm_config, dataset=dataset)

        graph = await load_graph()
        file_path = "examples/ags/scripts/data/hotpotqa.jsonl"
        
        score = await hotpotqa_evaluation(graph, file_path, samples, path)
        
        return score

    async def _mbpp_eval(self, graph_class, params, path, samples: int = 1):
        """
        Evaluate on MBPP dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="MBPP", llm_config=llm_config, dataset=dataset)

        graph = await load_graph()
        file_path = "examples/ags/scripts/data/mbpp-new.jsonl"
        
        score = await mbpp_evaluation(graph, file_path, samples, path)
        
        return score

    async def _drop_eval(self, graph_class, params, path):
        """
        Evaluate on DROP dataset.
        """
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            return graph_class(name="DROP", llm_config=llm_config, dataset=dataset)

        graph = await load_graph()
        file_path = "examples/ags/scripts/data/drop_dataset_dev.json"
        
        score = await drop_evaluation(graph, file_path, path)
        
        return score
