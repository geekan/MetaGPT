from __future__ import annotations

import json
from typing import List

from pydantic import BaseModel, Field

from metagpt.core.memory import Memory
from metagpt.core.schema import Message, Plan, Task, TaskResult

STRUCTURAL_CONTEXT = """
## User Requirement
{user_requirement}
## Context
{context}
## Current Plan
{tasks}
## Current Task
{current_task}
"""

PLAN_STATUS = """
## Finished Tasks
### code
```python
{code_written}
```

### execution result
{task_results}

## Current Task
{current_task}

## Finished Section of Current Task
### code
```python
{current_task_code}
```
### execution result
{current_task_result}

## Task Guidance
Write code for the incomplete sections of 'Current Task'. And avoid duplicating code from 'Finished Tasks' and 'Finished Section of Current Task', such as repeated import of packages, reading data, etc.
Specifically, {guidance}
"""


class BasePlanner(BaseModel):
    plan: Plan
    working_memory: Memory = Field(
        default_factory=Memory
    )  # memory for working on each task, discarded each time a task is done
    auto_run: bool = False

    def __init__(self, goal: str = "", plan: Plan = None, **kwargs):
        plan = plan or Plan(goal=goal)
        super().__init__(plan=plan, **kwargs)

    @property
    def current_task(self):
        return self.plan.current_task

    @property
    def current_task_id(self):
        return self.plan.current_task_id
    
    def get_useful_memories(self, task_exclude_field=None) -> list[Message]:
        """find useful memories only to reduce context length and improve performance"""
        user_requirement = self.plan.goal
        context = self.plan.context
        tasks = [task.dict(exclude=task_exclude_field) for task in self.plan.tasks]
        tasks = json.dumps(tasks, indent=4, ensure_ascii=False)
        current_task = self.plan.current_task.json() if self.plan.current_task else {}
        context = STRUCTURAL_CONTEXT.format(
            user_requirement=user_requirement, context=context, tasks=tasks, current_task=current_task
        )
        context_msg = [Message(content=context, role="user")]

        return context_msg + self.working_memory.get()

    async def update_plan(self, goal: str = "", max_tasks: int = 3, max_retries: int = 3):
        pass

    async def process_task_result(self, task_result: TaskResult):
        # ask for acceptance, users can other refuse and change tasks in the plan
        pass

    async def confirm_task(self, task: Task, task_result: TaskResult, review: str):
        pass

    def get_plan_status(self, exclude: List[str] = None) -> str:
        # prepare components of a plan status
        pass
