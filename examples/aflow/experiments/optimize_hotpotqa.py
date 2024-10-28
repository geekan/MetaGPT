# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 20:00 PM
# @Author  : didi
# @Desc    : Entrance of AFlow.

from metagpt.configs.models_config import ModelsConfig
from metagpt.ext.aflow.scripts.optimizer import DatasetType, Optimizer, QuestionType

# Crucial Parameters
dataset: DatasetType = "HotpotQA"  # Ensure the type is consistent with DatasetType
sample: int = 4  # Sample Count, which means how many workflows will be resampled from generated workflows
question_type: QuestionType = "qa"  # Ensure the type is consistent with QuestionType
optimized_path: str = "metagpt/ext/aflow/scripts/optimized"  # Optimized Result Save Path
initial_round: int = 1  # Corrected the case from Initial_round to initial_round
max_rounds: int = 20  # The max iteration of AFLOW.
check_convergence: bool = True  # Whether Early Stop
validation_rounds: int = 5  # The validation rounds of AFLOW.

# Config llm model, you can modify `config/config2.yaml` to use more llms.
mini_llm_config = ModelsConfig.default().get("gpt-4o-mini")
claude_llm_config = ModelsConfig.default().get("claude-3-5-sonnet-20240620")

# Config operators.
operators = [
    "Custom",  # It's basic unit of a fixed node. optimizer can modify its prompt to get vairous nodes.
    "AnswerGenerate",  # It's for qa
    # "CustomCodeGenerate",         # It's for code
    "ScEnsemble",  # It's for code, math and qa
    # "Test",                       # It's for code
    # "Programmer",  # It's for math
]

# Create an optimizer instance
optimizer = Optimizer(
    dataset=dataset,  # Config dataset
    question_type=question_type,  # Config Question Type
    opt_llm_config=claude_llm_config,  # Config Optimizer LLM
    exec_llm_config=mini_llm_config,  # Config Execution LLM
    check_convergence=check_convergence,  # Whether Early Stop
    operators=operators,  # Config Operators you want to use
    optimized_path=optimized_path,  # Config Optimized workflow's file path
    sample=sample,  # Only Top(sample) rounds will be selected.
    initial_round=initial_round,  # Optimize from initial round
    max_rounds=max_rounds,  # The max iteration of AFLOW.
    validation_rounds=validation_rounds,  # The validation rounds of AFLOW.
)

if __name__ == "__main__":
    # Optimize workflow via setting the optimizer's mode to 'Graph'
    optimizer.optimize("Graph")
    # Test workflow via setting the optimizer's mode to 'Test'
    # optimizer.optimize("Test")
