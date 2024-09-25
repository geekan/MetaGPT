# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 20:00 PM
# @Author  : didi
# @Desc    : Experiment of graph optimization

from examples.ags.scripts.optimizer import Optimizer
from metagpt.configs.models_config import ModelsConfig


# Crucial Parameters
dataset = "HumanEval"  # DatasetType
sample = 4  # Sample Count, which means how many workflows will be resampled from generated workflows
question_type = "code"  # Question Type
optimized_path = "examples/ags/scripts/optimized"  # Optimized Result Save Path

# Initialize LLM Model
mini_llm_config = ModelsConfig.default().get("gpt-4o-mini")
claude_llm_config = ModelsConfig.default().get("claude-3-5-sonnet-20240620")

# Initialize Operators List
operators = [
    "Custom",
    "CustomCodeGenerate",
    "ScEnsemble",
    "Test",
]

# Create an optimizer instance
optimizer = Optimizer(
    dataset=dataset,
    opt_llm_config=claude_llm_config,
    exec_llm_config=mini_llm_config,
    operators=operators,
    optimized_path=optimized_path,
    sample=sample,
    question_type=question_type,
)

# Run the optimizer
optimizer.optimize("Graph", 10)
# optimizer.optimize("Graph")
# optimizer.optimize("Operator")

