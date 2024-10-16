# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 20:00 PM
# @Author  : didi
# @Desc    : Experiment of graph optimization

from examples.aflow.scripts.optimizer import Optimizer
from metagpt.configs.models_config import ModelsConfig
from typing import Literal

# DatasetType, QuestionType, and OptimizerType definitions
DatasetType = Literal["HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP"]
QuestionType = Literal["math", "code", "quiz"]
OptimizerType = Literal["Graph", "Test"]

# Crucial Parameters
dataset: DatasetType = "GSM8K"  # Ensure the type is consistent with DatasetType
sample: int = 4  # Sample Count, which means how many workflows will be resampled from generated workflows
question_type: QuestionType = "math"  # Ensure the type is consistent with QuestionType
optimized_path: str = "examples/aflow/scripts/optimized"  # Optimized Result Save Path
initial_round: int = 1  # Corrected the case from Initial_round to initial_round
max_rounds: int = 20
check_convergence: bool = True

# Initialize LLM Model
four_o_llm_config = ModelsConfig.default().get("gpt-4o")
deepseek_llm_config = ModelsConfig.default().get("deepseek-chat")
mini_llm_config = ModelsConfig.default().get("gpt-4o-mini")
claude_llm_config = ModelsConfig.default().get("claude-3-5-sonnet-20240620")

# Initialize Operators List
operators = [
    "Custom"
]

# Create an optimizer instance
optimizer = Optimizer(
    dataset=dataset,
    question_type=question_type,
    opt_llm_config=claude_llm_config,
    exec_llm_config=mini_llm_config,
    check_convergence=check_convergence,
    operators=operators,
    optimized_path=optimized_path,
    sample=sample,
    initial_round=initial_round,
    max_rounds=max_rounds
)

if __name__ == "__main__":
    # Run the optimizer
    optimizer.optimize("Graph")
    # optimizer.optimize("Test")