
import json
from typing import Dict, List, Union

from metagpt.actions import Action
from metagpt.schema import Message, Task, Plan


TASK_GUIDE_PROMPT_TEMPLATE = """
# Context
{context}

##  Format example
1.
2.
3.
...

-----
Tasks are all code development tasks.
You are a professional engineer, the main goal is to plan out concise solution steps for Current Task before coding.
A planning process can reduce the difficulty and improve the quality of coding.
You may be given some code plans for the tasks ahead, but you don't have to follow the existing plan when planning the current task.
The output plan should following the subsequent principles:
1.The plan is a rough checklist of steps outlining the entire program's structure.Try to keep the number of steps fewer than 5.
2.The steps should be written concisely and at a high level, avoiding overly detailed implementation specifics.
3.The execution of the plan happens sequentially, but the plan can incorporate conditional (if) and looping(loop) keywords for more complex structures.
4.Output carefully referenced "Format example" in format.
"""

STRUCTURAL_CONTEXT = """
## User Requirement
{user_requirement}
## Current Plan
{tasks}
## Current Task
{current_task}
"""


class WriteTaskGuide(Action):

    async def run(self, plan: Plan) -> str:
        """Run of a task guide writing action, used in ml engineer

        Args:
            plan (plan): task plan
            useful_memories (list): useful_memories
        Returns:
            str: The dataset_descriptions string.
        """

        context = self.get_context(plan)
        task_guide_prompt = TASK_GUIDE_PROMPT_TEMPLATE.format(
            context=context,
        )
        task_guide = await self._aask(task_guide_prompt)
        return task_guide

    def get_context(self, plan: Plan):
        user_requirement = plan.goal
        task_rename_map = {
            'task_id': 'task_id',
            'instruction': 'instruction',
            'is_finished': 'is_finished',
            'task_guide': 'code_plan'
        }

        def process_task(task):
            task_dict = task.dict()
            ptask = {task_rename_map[k]: task_dict[k] for k in task_dict if k in task_rename_map}
            return ptask
        tasks = json.dumps(
            [process_task(task) for task in plan.tasks], indent=4, ensure_ascii=False
        )
        current_task = json.dumps(process_task(plan.current_task)) if plan.current_task else {}
        context = STRUCTURAL_CONTEXT.format(
            user_requirement=user_requirement, tasks=tasks, current_task=current_task
        )
        # print(context)
        return context

