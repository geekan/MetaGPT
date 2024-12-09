# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 20:00 PM
# @Author  : didi
# @Desc    : Entrance of AFlow.

import argparse
from typing import Dict, List

from metagpt.configs.models_config import ModelsConfig
from metagpt.ext.aflow.data.download_data import download
from metagpt.ext.aflow.scripts.optimizer import Optimizer


class ExperimentConfig:
    def __init__(self, dataset: str, question_type: str, operators: List[str]):
        self.dataset = dataset
        self.question_type = question_type
        self.operators = operators


EXPERIMENT_CONFIGS: Dict[str, ExperimentConfig] = {
    "DROP": ExperimentConfig(
        dataset="DROP",
        question_type="qa",
        operators=["Custom", "AnswerGenerate", "ScEnsemble"],
    ),
    "HotpotQA": ExperimentConfig(
        dataset="HotpotQA",
        question_type="qa",
        operators=["Custom", "AnswerGenerate", "ScEnsemble"],
    ),
    "MATH": ExperimentConfig(
        dataset="MATH",
        question_type="math",
        operators=["Custom", "ScEnsemble", "Programmer"],
    ),
    "GSM8K": ExperimentConfig(
        dataset="GSM8K",
        question_type="math",
        operators=["Custom", "ScEnsemble", "Programmer"],
    ),
    "MBPP": ExperimentConfig(
        dataset="MBPP",
        question_type="code",
        operators=["Custom", "CustomCodeGenerate", "ScEnsemble", "Test"],
    ),
    "HumanEval": ExperimentConfig(
        dataset="HumanEval",
        question_type="code",
        operators=["Custom", "CustomCodeGenerate", "ScEnsemble", "Test"],
    ),
}


def parse_args():
    parser = argparse.ArgumentParser(description="AFlow Optimizer")
    parser.add_argument(
        "--dataset",
        type=str,
        choices=list(EXPERIMENT_CONFIGS.keys()),
        required=True,
        help="Dataset type",
    )
    parser.add_argument("--sample", type=int, default=4, help="Sample count")
    parser.add_argument(
        "--optimized_path",
        type=str,
        default="metagpt/ext/aflow/scripts/optimized",
        help="Optimized result save path",
    )
    parser.add_argument("--initial_round", type=int, default=1, help="Initial round")
    parser.add_argument("--max_rounds", type=int, default=20, help="Max iteration rounds")
    parser.add_argument("--check_convergence", type=bool, default=True, help="Whether to enable early stop")
    parser.add_argument("--validation_rounds", type=int, default=5, help="Validation rounds")
    parser.add_argument(
        "--if_first_optimize",
        type=lambda x: x.lower() == "true",
        default=True,
        help="Whether to download dataset for the first time",
    )
    parser.add_argument(
        "--opt_model_name",
        type=str,
        default="claude-3-5-sonnet-20240620",
        help="Specifies the name of the model used for optimization tasks.",
    )
    parser.add_argument(
        "--exec_model_name",
        type=str,
        default="gpt-4o-mini",
        help="Specifies the name of the model used for execution tasks.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    config = EXPERIMENT_CONFIGS[args.dataset]

    models_config = ModelsConfig.default()
    opt_llm_config = models_config.get(args.opt_model_name)
    if opt_llm_config is None:
        raise ValueError(
            f"The optimization model '{args.opt_model_name}' was not found in the 'models' section of the configuration file. "
            "Please add it to the configuration file or specify a valid model using the --opt_model_name flag. "
        )

    exec_llm_config = models_config.get(args.exec_model_name)
    if exec_llm_config is None:
        raise ValueError(
            f"The execution model '{args.exec_model_name}' was not found in the 'models' section of the configuration file. "
            "Please add it to the configuration file or specify a valid model using the --exec_model_name flag. "
        )

    download(["datasets", "initial_rounds"], if_first_download=args.if_first_optimize)

    optimizer = Optimizer(
        dataset=config.dataset,
        question_type=config.question_type,
        opt_llm_config=opt_llm_config,
        exec_llm_config=exec_llm_config,
        check_convergence=args.check_convergence,
        operators=config.operators,
        optimized_path=args.optimized_path,
        sample=args.sample,
        initial_round=args.initial_round,
        max_rounds=args.max_rounds,
        validation_rounds=args.validation_rounds,
    )

    # Optimize workflow via setting the optimizer's mode to 'Graph'
    optimizer.optimize("Graph")

    # Test workflow via setting the optimizer's mode to 'Test'
    # optimizer.optimize("Test")
