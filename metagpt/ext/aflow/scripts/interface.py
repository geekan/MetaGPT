# -*- coding: utf-8 -*-
# @Date    : 2024-03-21
# @Author  : Your Name
# @Desc    : Interface for AFLOW

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Optional, Tuple

from metagpt.configs.models_config import ModelsConfig
from metagpt.ext.aflow.scripts.evaluator import DatasetType
from metagpt.ext.aflow.scripts.optimizer_utils.data_utils import DataUtils
from metagpt.logs import logger


def load_best_round(dataset: str, optimized_path: str = "metagpt/ext/aflow/scripts/optimized") -> int:
    """加载最佳表现的轮次"""
    data_utils = DataUtils(f"{optimized_path}/{dataset}")

    # 使用get_top_rounds获取得分最高的轮次
    top_rounds = data_utils.get_top_rounds(sample=2, mode="Graph")
    if not top_rounds[1]:
        return 1

    return top_rounds[1]["round"]


def load_workflow_class(graph_path: str):
    """动态加载工作流类"""
    spec = importlib.util.spec_from_file_location("workflow_module", graph_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["workflow_module"] = module
    spec.loader.exec_module(module)
    return module.Workflow


async def aflow_inference(
    dataset: DatasetType,
    question: str,
    entry_point: Optional[str] = None,
    round: Optional[int] = None,
    llm_name: str = "gpt-4o-mini",
    optimized_path: str = "metagpt/ext/aflow/scripts/optimized",
) -> Tuple[str, float]:
    """AFLOW推理接口

    Args:
        dataset: 数据集名称
        question: 输入问题
        round: 指定使用的轮次，如果为None则使用最佳轮次
        llm_name: 使用的LLM模型名称
        optimized_path: 优化结果保存路径

    Returns:
        (答案, 成本)的元组
    """
    # 如果没有指定轮次，使用最佳轮次
    if round is None:
        round = load_best_round(dataset, optimized_path)

    logger.info(f"Using round {round} for inference")

    # 构建工作流路径并加载
    graph_path = Path(optimized_path) / dataset / "workflows" / f"round_{round}" / "graph.py"
    if not graph_path.exists():
        raise FileNotFoundError(f"Workflow file not found: {graph_path}")

    # 动态加载工作流类
    WorkflowClass = load_workflow_class(str(graph_path))

    # 创建工作流实例
    llm_config = ModelsConfig.default().get(llm_name)
    workflow = WorkflowClass(
        name=f"{dataset}_workflow",
        llm_config=llm_config,
        dataset=dataset,
    )

    # 执行推理
    if dataset in ["MBPP", "HumanEval"]:
        # 代码类任务需要额外的entry_point参数
        answer, cost = await workflow(question, entry_point=entry_point)
    else:
        answer, cost = await workflow(question)

    return answer, cost


if __name__ == "__main__":
    asyncio.run(
        aflow_inference(
            dataset="MBPP",
            question="write a function named add_two_numbers to calculate the sum of two numbers",
            entry_point="add_two_numbers",
        )
    )
