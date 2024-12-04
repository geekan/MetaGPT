import os
import fire
import asyncio
import json
import argparse
import shutil
from typing import Optional
from metagpt.llm import LLM

from metagpt.ext.sela.data.custom_task import get_mle_is_lower_better, get_mle_task_id
from metagpt.ext.sela.runner.autogluon import GluonRunner
from metagpt.ext.sela.runner.autosklearn import AutoSklearnRunner
from metagpt.ext.sela.runner.custom import CustomRunner
from metagpt.ext.sela.runner.mcts import MCTSRunner
from metagpt.ext.sela.runner.random_search import RandomSearchRunner
from metagpt.ext.sela.runner.runner import Runner

from metagpt.ext.sela.evaluation.evaluation import (
    node_evaluate_score_mlebench,
    node_evaluate_score_sela,
)
from metagpt.ext.sela.evaluation.visualize_mcts import get_tree_text
from metagpt.ext.sela.runner.runner import Runner
from metagpt.ext.sela.search.search_algorithm import MCTS, Greedy, Random


class Sela:
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
        "from_scratch": False,
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

    def __init__(self, use_llm: bool = True):
        """
        初始化 Sela 类。

        Args:
            use_llm: 是否使用 LLM 来解析 requirement。
        """
        self.llm = LLM() if use_llm else None

    async def _parse_requirement(self, requirement: str) -> dict:
        """
        使用 LLM 分析实验需求，提取实验配置和实验数据信息。

        Args:
            requirement: 用户输入的实验需求描述。

        Returns:
            dict: 包含实验配置和实验数据信息的字典。
        """
        if not self.llm:
            raise ValueError("LLM is not initialized. Cannot parse the requirement.")

        # 确保 `requirement` 是安全的字符串
        sanitized_requirement = json.dumps(requirement)  # 将字符串转为 JSON 安全字符串

        prompt = f"""
        You are an assistant that helps configure machine learning experiments.

        Given the following requirement:
        {sanitized_requirement}

        Your task:
        1. Extract **experiment configurations** from the requirement if they are explicitly mentioned.
           For example, "rollouts: 10", "exp_mode: mcts", or "max_depth: 4". These should override default values.
        2. Extract **experiment data information** from the requirement. This includes:
           - **dataset**: The name of the dataset being used (e.g., "04_titanic").
           - **metric**: The evaluation metric or scoring method mentioned (e.g., "f1", "rmse", "f1 weighted").
           - **target_col**: Predict the target column `Survived` (e.g., "Survived").
           - **user_requirement**: Any specific instructions or requirements for handling the dataset (e.g.,"Your goal is to predict the target column `Survived`."
                   "Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. "
                   "Report f1 on the eval data. Do not plot or make any visualizations.")

        Output a JSON object containing two parts:
        - "config": This is a dictionary containing the experiment configuration. Include only explicitly mentioned configurations. Use keys like:
          - "task": str (e.g., "titanic")
          - "exp_mode": str (e.g., "mcts", "rs", "base", "custom", "greedy", "autogluon", "random", "autosklearn")
          - "rollouts": int
          - "max_depth": int
          - "rs_mode": str (e.g., "single", "set")
          - "special_instruction": str (e.g., "text", "image")
        - "data_info": This is a dictionary containing the experiment data information with keys:
          - "dataset": str (e.g., "04_titanic")
          - "metric": str (e.g., "f1", "rmse", "f1 weighted")
          - "target_col": str (e.g., "Survived")
          - "user_requirement": str (e.g., Your goal is to predict the target column `Survived`."
                   "Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. "
                   "Report f1 on the eval data. Do not plot or make any visualizations.")

        Example output:
        {{
          "config": {{
            "task": "titanic",
            "exp_mode": "mcts",
            "rollouts": 10
          }},
          "data_info": {{
            "dataset": "04_titanic",
            "metric": "f1",
            "target_col": "Predict the target column Survived",
            "user_requirement": Your goal is to predict the target column `Survived`. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. "
                   "Report f1 on the eval data. Do not plot or make any visualizations."
          }}
        }}

        Return only the JSON object. Do not include any comments or extra text.
        """
        response = await self.llm.aask(prompt)
        print(f"LLM Response: {response}")

        parsed_response = self._parse_json(response)
        config_from_user = parsed_response.get("config", {})
        data_info = parsed_response.get("data_info", {})

        # 合并默认配置和用户提供的配置
        config = {**self.DEFAULT_CONFIG, **config_from_user}
        return {"config": config, "data_info": data_info}

    @staticmethod
    def _parse_json(json_string: str) -> dict:
        """
        解析 JSON 字符串，去除可能的 Markdown 标记。
        """
        json_string = json_string.strip()
        if json_string.startswith("```json"):
            json_string = json_string[7:].strip()
        if json_string.endswith("```"):
            json_string = json_string[:-3].strip()

        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format: {json_string}")

    def _select_runner(self, config: argparse.Namespace, data_config: dict):
        """
        根据配置选择适当的实验执行器。

        Args:
            config: 从 LLM 解析出的实验配置。

        Returns:
            实验执行器实例。
        """
        exp_mode = config.exp_mode
        if exp_mode == "mcts":
            return MCTSRunner(config, data_config)
        elif exp_mode == "greedy":
            return MCTSRunner(tree_mode="greedy")
        elif exp_mode == "random":
            return MCTSRunner(tree_mode="random")
        elif exp_mode == "rs":
            return RandomSearchRunner(config)
        elif exp_mode == "base":
            return Runner(config)
        elif exp_mode == "custom":
            return CustomRunner(config)
        else:
            raise ValueError(f"Invalid exp_mode: {exp_mode}")

    async def run(self, requirement: str, data_dir: Optional[str] = None):
        """
        Args:
            requirement: 实验需求，描述目标任务。
            data_dir: 数据目录。
        """
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

        # 使用 LLM 解析需求
        config_all = await self._parse_requirement(requirement)
        config_exp = config_all["config"]
        data_info = config_all["data_info"]

        # 构造默认的 data_config 文件
        data_config = {
            "datasets_dir": data_dir,  # 用户输入的数据目录路径
            "work_dir": "../../workspace",  # 默认的工作目录
            "role_dir": "storage/SELA",  # 存储角色路径
            "datasets": {config_exp.get("task"): data_info},  # 数据集信息
        }

        # 根据需求选择适当的实验执行器
        runner = self._select_runner(argparse.Namespace(**config_exp), data_config)

        # 运行实验
        await runner.run_experiment()


async def main():
    """
    Main 函数作为入口，支持直接运行。
    """
    # 示例需求和数据路径
    requirement = ("Optimize 04_titanic dataset using MCTS with 10 rollouts. "
                   "Your goal is to predict the target column `Survived`."
                   "Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. "
                   "Report f1 on the eval data. Do not plot or make any visualizations.")

    data_dir = "/home/coder/project/chenxin/MetaGPT/metagpt/ext/sela/data/SELA-datasets"

    # 初始化 Sela 并运行
    sela = Sela()
    await sela.run(requirement, data_dir)


if __name__ == "__main__":
    fire.Fire(main)
