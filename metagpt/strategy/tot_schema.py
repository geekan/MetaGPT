# -*- coding: utf-8 -*-
# @Date    : 12/25/2023 9:14 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

from enum import Enum

from pydantic import BaseModel, Field

from metagpt.strategy.base import BaseEvaluator, BaseParser


class MethodSelect(Enum):
    """Enumeration for method selection strategies.

    Attributes:
        SAMPLE: Represents the 'sample' selection method.
        GREEDY: Represents the 'greedy' selection method.
    """

    SAMPLE = "sample"
    GREEDY = "greedy"


class Strategy(Enum):
    """Enumeration for search strategies.

    Attributes:
        BFS: Represents the Breadth-First Search strategy.
        DFS: Represents the Depth-First Search strategy.
        MCTS: Represents the Monte Carlo Tree Search strategy.
    """

    BFS = "BFS"
    DFS = "DFS"
    MCTS = "MCTS"


class ThoughtSolverConfig(BaseModel):
    """Configuration model for ThoughtSolver.

    Attributes:
        max_steps: Maximum number of steps to take.
        method_select: Method for selecting actions.
        n_generate_sample: Number of samples to generate.
        n_select_sample: Number of samples to select from generated samples.
        n_solution_sample: Number of samples to consider as potential solutions.
        parser: Parser to use for processing input.
        evaluator: Evaluator to use for assessing potential solutions.
    """

    max_steps: int = 3
    method_select: str = MethodSelect.GREEDY  # ["sample"/"greedy"]
    n_generate_sample: int = 5  # per node
    n_select_sample: int = 3  # per path
    n_solution_sample: int = 5  # only for dfs
    parser: BaseParser = Field(default_factory=BaseParser)
    evaluator: BaseEvaluator = Field(default_factory=BaseEvaluator)
