import argparse
import json
import os
from typing import Optional

from metagpt.ext.sela.runner.custom import CustomRunner
from metagpt.ext.sela.runner.mcts import MCTSRunner
from metagpt.ext.sela.runner.random_search import RandomSearchRunner
from metagpt.ext.sela.runner.runner import Runner
from metagpt.llm import LLM
from metagpt.utils.common import CodeParser

SELA_INSTRUCTION = """
You are an assistant for configuring machine learning experiments.

Given the requirement and data directory:
{requirement}
{data_dir}

Your task:
1. Extract **experiment configurations** from the requirement if explicitly mentioned, such as:
   - "rollouts: 10"
   - "exp_mode: mcts"
   - "max_depth: 4"

2. Extract **experiment data information**, including:
   - **dataset**: Dataset name (if explicitly mentioned in the requirement, use that; otherwise, use the last folder name in the data directory path)
   - **metric**: Evaluation metric
   - **target_col**: Target column
   - **user_requirement**: Specific instructions or dataset handling requirements 

Output a JSON object with two parts:
- "config": A dictionary of explicitly mentioned configurations, using keys:
  - "task": str (a noun based on the dataset name, customizable, e.g., "titanic")
  - "exp_mode": str (e.g., "mcts", "rs", "base", "custom", "greedy", "autogluon")
  - "rollouts": int
  - "max_depth": int
  - "rs_mode": str (e.g., "single", "set")
  - "special_instruction": str (e.g., "text", "image")
- "data_info": A dictionary of experiment data information, with keys:
  - "dataset": str (e.g., "04_titanic")
  - "metric": str (e.g., "f1", "rmse")
  - "target_col": str (e.g., "Survived")
  - "user_requirement": str 

Example output:
```json
{{
  "config": {{
    "task": "titanic",
    "exp_mode": "mcts",
    "rollouts": 10
  }},
  "data_info": {{
    "dataset": "04_titanic",
    "metric": "f1",
    "target_col": "Survived",
    "user_requirement": "Predict the target column `Survived`. Perform data analysis, preprocessing, feature engineering, and modeling. Report f1 on eval data. Do not include visualizations."
  }}
}}
```

Return only the JSON object.
"""
DEFAULT_CONFIG = {
    "name": "",
    "reflection": True,
    "no_reflection": False,
    "exp_mode": "mcts",
    "rollouts": 10,
    "load_tree": False,
    "role_timeout": 1000,
    "use_fixed_insights": False,
    "low_is_better": False,
    "start_task_id": 2,
    "from_scratch": True,
    "eval_func": "sela",
    "custom_dataset_dir": None,
    "max_depth": 4,
    "rs_mode": "single",
    "is_multimodal": True,
    "num_experiments": 1,
    "external_eval": True,
    "no_external_eval": False,
    "special_instruction": None,
}


class SELA:
    def __init__(self, use_llm: bool = True):
        """
        Initialize the SELA class.
        Args:
            use_llm: Whether to use LLM (Language Model) to parse the requirement.
        """
        self.llm = LLM() if use_llm else None

    async def _parse_requirement(self, requirement: str, data_dir: str) -> dict:
        """
        Use LLM to analyze the experiment requirement and extract configurations.
        """
        if not self.llm:
            raise ValueError("LLM is not initialized. Cannot parse the requirement.")
        response = await self.llm.aask(
            SELA_INSTRUCTION.format(requirement=json.dumps(requirement), data_dir=json.dumps(data_dir))
        )
        print(f"LLM Response: {response}")
        parsed_response = self._parse_json(response)
        return {
            "config": {**DEFAULT_CONFIG, **parsed_response.get("config", {})},
            "data_info": parsed_response.get("data_info", {}),
        }

    @staticmethod
    def _parse_json(json_string: str) -> dict:
        """
        Extract and parse JSON content from the given string using CodeParser.
        """
        try:
            json_code = CodeParser.parse_code("", json_string, "json")
            import json

            return json.loads(json_code)
        except ValueError:
            raise ValueError(f"Invalid JSON format: {json_string}")

    def _select_runner(self, config: argparse.Namespace, data_config: dict):
        """
        Select the appropriate experiment runner based on the experiment mode.
        """
        runners = {
            "mcts": lambda: MCTSRunner(config, data_config),
            "greedy": lambda: MCTSRunner(tree_mode="greedy"),
            "random": lambda: MCTSRunner(tree_mode="random"),
            "rs": lambda: RandomSearchRunner(config),
            "base": lambda: Runner(config),
            "custom": lambda: CustomRunner(config),
        }
        if config.exp_mode not in runners:
            raise ValueError(f"Invalid exp_mode: {config.exp_mode}")
        return runners[config.exp_mode]()

    async def run(self, requirement: str, data_dir: Optional[str] = None):
        """
        Run the experiment with the given requirement and data directory.
        """
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

        config_all = await self._parse_requirement(requirement, data_dir)
        config_exp, data_info = config_all["config"], config_all["data_info"]

        data_config = {
            "datasets_dir": data_dir,
            "work_dir": "../../workspace",
            "role_dir": "storage/SELA",
            "datasets": {config_exp.get("task"): data_info},
        }

        await self._select_runner(argparse.Namespace(**config_exp), data_config).run_experiment()
