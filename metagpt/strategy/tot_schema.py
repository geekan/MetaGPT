# -*- coding: utf-8 -*-
# @Date    : 12/25/2023 9:14 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from enum import Enum

from pydantic import BaseModel, Field

from metagpt.strategy.base import BaseEvaluator, BaseParser


class MethodSelect(Enum):
    SAMPLE = "sample"
    GREEDY = "greedy"


class Strategy(Enum):
    BFS = "BFS"
    DFS = "DFS"
    MCTS = "MCTS"


class ThoughtSolverConfig(BaseModel):
    max_steps: int = 3
    method_select: str = MethodSelect.GREEDY  # ["sample"/"greedy"]
    n_generate_sample: int = 5  # per node
    n_select_sample: int = 3  # per path
    n_solution_sample: int = 5  # only for dfs
    parser: BaseParser = Field(default_factory=BaseParser)
    evaluator: BaseEvaluator = Field(default_factory=BaseEvaluator)
