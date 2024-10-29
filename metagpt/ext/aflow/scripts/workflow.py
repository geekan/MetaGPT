# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 22:07 PM
# @Author  : didi
# @Desc    : Basic Graph Class


from metagpt.ext.aflow.scripts.evaluator import DatasetType
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager


class Workflow:
    def __init__(
        self,
        name: str,
        llm_config,
        dataset: DatasetType,
    ) -> None:
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.llm.cost_manager = CostManager()

    async def __call__(self, problem: str):
        """
        Implementation of the workflow
        """
        raise NotImplementedError("This method should be implemented by the subclass")
