# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 20:00 PM
# @Author  : didi
# @Desc    : Entrance of AFlow.

import argparse

from metagpt.configs.models_config import ModelsConfig
from metagpt.ext.aflow.scripts.evaluator import Optimizer


def parse_args():
    parser = argparse.ArgumentParser(description="AFlow Optimizer for MATH")
    parser.add_argument("--dataset", type=str, default="MATH", help="Dataset type")
    parser.add_argument("--sample", type=int, default=4, help="Sample count")
    parser.add_argument("--question_type", type=str, default="math", help="Question type")
    parser.add_argument(
        "--optimized_path", type=str, default="metagpt/ext/aflow/scripts/optimized", help="Optimized result save path"
    )
    parser.add_argument("--initial_round", type=int, default=1, help="Initial round")
    parser.add_argument("--max_rounds", type=int, default=20, help="Max iteration rounds")
    parser.add_argument("--check_convergence", type=bool, default=True, help="Whether to enable early stop")
    parser.add_argument("--validation_rounds", type=int, default=5, help="Validation rounds")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    mini_llm_config = ModelsConfig.default().get("gpt-4o-mini")
    claude_llm_config = ModelsConfig.default().get("claude-3-5-sonnet-20240620")

    operators = [
        "Custom",
        "ScEnsemble",
        "Programmer",
    ]

    optimizer = Optimizer(
        dataset=args.dataset,
        question_type=args.question_type,
        opt_llm_config=claude_llm_config,
        exec_llm_config=mini_llm_config,
        check_convergence=args.check_convergence,
        operators=operators,
        optimized_path=args.optimized_path,
        sample=args.sample,
        initial_round=args.initial_round,
        max_rounds=args.max_rounds,
        validation_rounds=args.validation_rounds,
    )

    optimizer.optimize("Graph")
