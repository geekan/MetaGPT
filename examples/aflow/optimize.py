# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 20:00 PM
# @Author  : didi
# @Desc    : Entrance of AFlow.

import argparse

from metagpt.configs.models_config import ModelsConfig
from metagpt.ext.aflow.data.download_data import download
from metagpt.ext.aflow.scripts.optimizer import Optimizer


def parse_args():
    parser = argparse.ArgumentParser(description="AFlow Optimizer")
    parser.add_argument(
        "--dataset",
        type=str,
        default="MATH",
        help="Dataset type, including HumanEval, MBPP, GSM8K, MATH, HotpotQA, DROP",
    )
    parser.add_argument("--sample", type=int, default=4, help="Sample count")
    parser.add_argument("--question_type", type=str, default="math", help="Question type, including math, code, qa")
    parser.add_argument(
        "--optimized_path", type=str, default="metagpt/ext/aflow/scripts/optimized", help="Optimized result save path"
    )
    parser.add_argument("--initial_round", type=int, default=1, help="Initial round")
    parser.add_argument("--max_rounds", type=int, default=20, help="Max iteration rounds")
    parser.add_argument("--check_convergence", type=bool, default=True, help="Whether to enable early stop")
    parser.add_argument("--validation_rounds", type=int, default=5, help="Validation rounds")
    parser.add_argument("--if_first_optimize", type=bool, default=True, help="Whether this is first optimization")
    return parser.parse_args()


# Config llm model, you can modify `config/config2.yaml` to use more llms.
mini_llm_config = ModelsConfig.default().get("gpt-4o-mini")
claude_llm_config = ModelsConfig.default().get("claude-3-5-sonnet-20240620")

# Config operators.
operators = [
    "Custom",  # It's basic unit of a fixed node. optimizer can modify its prompt to get vairous nodes.
    # "AnswerGenerate",              # It's for qa
    # "CustomCodeGenerate",         # It's for code
    "ScEnsemble",  # It's for code, math and qa
    # "Test",                       # It's for code
    "Programmer",  # It's for math
]

if __name__ == "__main__":
    args = parse_args()

    # Create an optimizer instance
    optimizer = Optimizer(
        dataset=args.dataset,  # Config dataset
        question_type=args.question_type,  # Config Question Type
        opt_llm_config=claude_llm_config,  # Config Optimizer LLM
        exec_llm_config=mini_llm_config,  # Config Execution LLM
        check_convergence=args.check_convergence,  # Whether Early Stop
        operators=operators,  # Config Operators you want to use
        optimized_path=args.optimized_path,  # Config Optimized workflow's file path
        sample=args.sample,  # Only Top(sample) rounds will be selected.
        initial_round=args.initial_round,  # Optimize from initial round
        max_rounds=args.max_rounds,  # The max iteration of AFLOW.
        validation_rounds=args.validation_rounds,  # The validation rounds of AFLOW.
    )

    # When you fisrt use, please download the datasets and initial rounds; If you want to get a look of the results, please download the results.
    download(["datasets", "initial_rounds"], if_first_download=args.if_first_optimize)
    # Optimize workflow via setting the optimizer's mode to 'Graph'
    optimizer.optimize("Graph")
    # Test workflow via setting the optimizer's mode to 'Test'
    # optimizer.optimize("Test")
