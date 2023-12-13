
import json
from typing import Dict, List, Union

from metagpt.actions import Action
from metagpt.schema import Message, Task, Plan
from metagpt.utils.common import CodeParser

# CODE_STEPS_PROMPT_TEMPLATE = """
# # Context
# {context}
#
# -----
# Tasks are all code development tasks.
# You are a professional engineer, the main goal is to plan out concise solution steps for Current Task before coding.
# A planning process can reduce the difficulty and improve the quality of coding.
# You may be given some code plans for the tasks ahead, but you don't have to follow the existing plan when planning the current task.
# The output plan should following the subsequent principles:
# 1.The plan is a rough checklist of steps outlining the entire program's structure.Try to keep the number of steps fewer than 5.
# 2.The steps should be written concisely and at a high level, avoiding overly detailed implementation specifics.
# 3.The execution of the plan happens sequentially, but the plan can incorporate conditional (if) and looping(loop) keywords for more complex structures.
#
# Output the code steps in a JSON format, as shown in this example:
# ```json
# {
#     "Step 1": "",
#     "Step 2": "",
#     "Step 3": "",
#     ...
# }
# ```
# """

CODE_STEPS_PROMPT_TEMPLATE = """
# Context
{context}

-----
Tasks are all code development tasks.
You are a professional engineer, the main goal is to plan out concise solution steps for Current Task before coding.
A planning process can reduce the difficulty and improve the quality of coding.
You may be given some code plans for the tasks ahead, but you don't have to follow the existing plan when planning the current task.
The output plan should following the subsequent principles:
1.The plan is a rough checklist of steps outlining the entire program's structure.Try to keep the number of steps fewer than 5.
2.The steps should be written concisely and at a high level, avoiding overly detailed implementation specifics.
3.The execution of the plan happens sequentially, but the plan can incorporate conditional (if) and looping(loop) keywords for more complex structures.
4.Follow the code logic to design and provide the code steps. You can analysis it step by step

Output the code steps in a JSON format, as shown in this example:
```json
{
    "Step 1": "",
    "Step 2": "",
    "Step 3": "",
    ...
}
```
"""

# STRUCTURAL_CONTEXT = """
# ## User Requirement
# {user_requirement}
# ## Current Plan
# {tasks}
# ## Current Task
# {current_task}
# """

STRUCTURAL_CONTEXT = """
## User Requirement
{user_requirement}
## Plan
{tasks}
## Codes
{codes}
## Current Task
{current_task}
"""


class WriteCodeSteps(Action):

    async def run(self, plan: Plan) -> str:
        """Run of a task guide writing action, used in ml engineer

        Args:
            plan (plan): task plan
            useful_memories (list): useful_memories
        Returns:
            str: The dataset_descriptions string.
        """

        context = self.get_context(plan)
        code_steps_prompt = CODE_STEPS_PROMPT_TEMPLATE.replace(
            "{context}", context
        )
        code_steps = await self._aask(code_steps_prompt)
        code_steps = CodeParser.parse_code(block=None, text=code_steps)
        return code_steps

    def get_context(self, plan: Plan):
        user_requirement = plan.goal
        # select_task_keys = ['task_id', 'instruction', 'is_finished', 'code']
        select_task_keys = ['task_id','instruction']
        
        def process_task(task):
            task_dict = task.dict()
            ptask = {k: task_dict[k] for k in task_dict if k in select_task_keys }
            return ptask
        
        
        tasks = json.dumps(
            [process_task(task) for task in plan.tasks], indent=4, ensure_ascii=False
        )
        
        code_lists = [task.code for task in plan.tasks if task.is_finished==True]
        codes = "\n\n".join(code_lists)
        current_task = json.dumps(process_task(plan.current_task)) if plan.current_task else {}
        context = STRUCTURAL_CONTEXT.format(
            user_requirement=user_requirement, tasks=tasks, codes=codes, current_task=current_task
        )
        print(context)
        # print(context)
        return context
