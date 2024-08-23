# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 22:07 PM
# @Author  : didi
# @Desc    : Basic Graph Class

from typing import Literal

from metagpt.llm import LLM
from metagpt.utils.cost_manager import CostManager

DatasetType = Literal["humaneval", "gsm8k", "hotpotqa", "drop", "mmlu"]

cost_manager = CostManager()


class Graph:
    def __init__(
        self,
        name: str,
        llm: LLM,
        dataset: DatasetType,
    ) -> None:
        self.name = name
        self.model = llm
        self.dataset = dataset
        self.cost = cost_manager  # TODO

    def __call__():
        """
        Implementation of the graph
        """
        NotImplementedError("Subclasses must implement __call__ method")
