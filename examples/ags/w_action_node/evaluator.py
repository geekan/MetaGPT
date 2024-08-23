# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : evaluate for different dataset
from typing import Literal

# TODO 完成实验数据集的手动划分

DatasetType = Literal["HumanEval", "MMBP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]


class Evaluator:
    """
    在这里完成对不同数据集的评估
    """

    def __init__(self, eval_path: str):
        pass

    def validation_evaluate(self, dataset: DatasetType):
        """
        Evaluates on validation dataset.
        """
        pass

    def test_evaluate(self, dataset: DatasetType):
        """
        Evaluates on test dataset.
        """
        pass
