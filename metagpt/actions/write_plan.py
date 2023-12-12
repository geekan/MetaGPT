# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 11:24:03
@Author  :   orange-crow
@File    :   plan.py
"""
from typing import List, Dict, Tuple
import json
from copy import deepcopy
import traceback

from metagpt.actions import Action
from metagpt.prompts.ml_engineer import ASSIGN_TASK_TYPE_PROMPT, ASSIGN_TASK_TYPE
from metagpt.schema import Message, Task, Plan
from metagpt.utils.common import CodeParser, create_func_config


class WritePlan(Action):
    PROMPT_TEMPLATE = """
    # Context:
    __context__
    # Task:
    Based on the context, write a plan or modify an existing plan of what you should do to achieve the goal. A plan consists of one to __max_tasks__ tasks.
    If you are modifying an existing plan, carefully follow the instruction, don't make unnecessary changes. Give the whole plan unless instructed to modify only one task of the plan.
    Output a list of jsons following the format:
    ```json
    [
        {
            "task_id": str = "unique identifier for a task in plan, can be an ordinal",
            "dependent_task_ids": list[str] = "ids of tasks prerequisite to this task",
            "instruction": "what you should do in this task, one short phrase or sentence",
        },
        ...
    ]
    ```
    """

    async def assign_task_type(self, tasks: List[Dict]) -> str:
        """Assign task type to each task in tasks

        Args:
            tasks (List[Dict]): tasks to be assigned task type

        Returns:
            List[Dict]: tasks with task type assigned
        """
        task_list = "\n".join(
            [f"Task {task['task_id']}: {task['instruction']}" for task in tasks]
        )
        prompt = ASSIGN_TASK_TYPE_PROMPT.format(task_list=task_list)
        tool_config = create_func_config(ASSIGN_TASK_TYPE)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        task_type_list = rsp["task_type"]
        for task, task_type in zip(tasks, task_type_list):
            task["task_type"] = task_type
        return json.dumps(tasks)

    async def run(
        self, context: List[Message], max_tasks: int = 5, use_tools: bool = False
    ) -> str:
        prompt = (
            self.PROMPT_TEMPLATE.replace("__context__", "\n".join([str(ct) for ct in context]))
            # .replace("__current_plan__", current_plan)
            .replace("__max_tasks__", str(max_tasks))
        )
        rsp = await self._aask(prompt)
        rsp = CodeParser.parse_code(block=None, text=rsp)
        if use_tools:
            rsp = await self.assign_task_type(json.loads(rsp))
        return rsp

def rsp_to_tasks(rsp: str) -> List[Task]:
    rsp = json.loads(rsp)
    tasks = [Task(**task_config) for task_config in rsp]
    return tasks

def update_plan_from_rsp(rsp: str, current_plan: Plan):
    tasks = rsp_to_tasks(rsp)
    if len(tasks) == 1:
        # handle a single task
        if current_plan.has_task_id(tasks[0].task_id):
            # replace an existing task
            current_plan.replace_task(tasks[0])
        else:
            # append one task
            current_plan.append_task(tasks[0])

    else:
        # add tasks in general
        current_plan.add_tasks(tasks)

def precheck_update_plan_from_rsp(rsp: str, current_plan: Plan) -> Tuple[bool, str]:
    temp_plan = deepcopy(current_plan)
    try:
        update_plan_from_rsp(rsp, temp_plan)
        return True, ""
    except Exception as e:
        return False, e
