# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 11:24:03
@Author  :   orange-crow
@File    :   plan.py
"""
from metagpt.actions import Action
from metagpt.prompts.plan import TASK_PLAN_SYSTEM_MSG
from metagpt.schema import Message


class Plan(Action):
    def __init__(self, llm=None):
        super().__init__("", None, llm)

    async def run(self, prompt: str, role: str = None, system_msg: str = None) -> str:
        if role:
            system_msg = TASK_PLAN_SYSTEM_MSG.format(role=role)
        rsp = await self._aask(system_msg + prompt)
        return Message(rsp, role="assistant", sent_from=self.__class__.__name__)
