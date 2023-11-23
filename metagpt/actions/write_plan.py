# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 11:24:03
@Author  :   orange-crow
@File    :   plan.py
"""
from typing import List
import json

from metagpt.actions import Action
from metagpt.schema import Message, Task

class WritePlan(Action):
    PROMPT_TEMPLATE = """
    # Context:
    __context__
    # Current Plan:
    __current_plan__
    # Task:
    Based on the context, write a plan or modify an existing plan of what you should do to achieve the goal. A plan consists of one to __max_tasks__ tasks.
    If you are modifying an existing plan, carefully follow the instruction, don't make unnecessary changes.
    Output a list of jsons following the format:
    [
        {
            "task_id": str = "unique identifier for a task in plan, can be a ordinal",
            "dependent_task_ids": list[str] = "ids of tasks prerequisite to this task",
            "instruction": "what you should do in this task, one short phrase or sentence",
        },
        ...
    ]
    """
    async def run(self, context: List[Message], current_plan: str = "", max_tasks: int = 5) -> str:
        prompt = (
            self.PROMPT_TEMPLATE.replace("__context__", "\n".join([str(ct) for ct in context]))
            .replace("__current_plan__", current_plan).replace("__max_tasks__", str(max_tasks))
        )
        rsp = await self._aask(prompt)
        return rsp

    @staticmethod
    def rsp_to_tasks(rsp: str) -> List[Task]:
        rsp = json.loads(rsp)
        tasks = [Task(**task_config) for task_config in rsp]
        return tasks
