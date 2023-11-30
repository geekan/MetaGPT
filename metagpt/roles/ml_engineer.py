from typing import Dict, List, Union
import json
import subprocess

import fire
import re

from metagpt.roles import Role
from metagpt.actions import Action
from metagpt.schema import Message, Task, Plan
from metagpt.logs import logger
from metagpt.actions.write_plan import WritePlan
from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools
from metagpt.actions.execute_code import ExecutePyCode

STRUCTURAL_CONTEXT = """
## User Requirement
{user_requirement}
## Current Plan
{tasks}
## Current Task
{current_task}
"""


def truncate(result: str, keep_len: int = 1000) -> str:
    desc = "Truncated to show only the last 1000 characters\n"
    if result.startswith(desc):
        result = result[-len(desc) :]

    if len(result) > keep_len:
        result = result[-keep_len:]

    if not result.startswith(desc):
        return desc + result
    return desc


def remove_escape_and_color_codes(input_str):
    # 使用正则表达式去除转义字符和颜色代码
    pattern = re.compile(r'\x1b\[[0-9;]*[mK]')
    result = pattern.sub('', input_str)
    return result


class AskReview(Action):
    async def run(self, context: List[Message], plan: Plan = None):
        logger.info("Current overall plan:")
        logger.info(
            "\n".join([f"{task.task_id}: {task.instruction}, is_finished: {task.is_finished}" for task in plan.tasks])
        )

        logger.info("most recent context:")
        latest_action = context[-1].cause_by.__name__ if context[-1].cause_by else ""
        prompt = f"\nPlease review output from {latest_action}:\n" \
            "If you want to change a task in the plan, say 'change task task_id, ... (things to change)'\n" \
            "If you confirm the output and wish to continue with the current process, type CONFIRM\n" \
            "If you want to terminate the process, type exit:\n"
        rsp = input(prompt)

        if rsp.lower() in ("exit"):
            exit()

        confirmed = rsp.lower() in ("confirm", "yes", "y")

        return rsp, confirmed


class WriteTaskGuide(Action):
    async def run(self, task_instruction: str, data_desc: str = "") -> str:
        return ""


class MLEngineer(Role):
    def __init__(
        self, name="ABC", profile="MLEngineer", goal="", auto_run: bool = False
    ):
        super().__init__(name=name, profile=profile, goal=goal)
        self._set_react_mode(react_mode="plan_and_act")
        self.plan = Plan(goal=goal)
        self.use_tools = False
        self.use_task_guide = False
        self.execute_code = ExecutePyCode()
        self.auto_run = auto_run

    async def _plan_and_act(self):
        # create initial plan and update until confirmation
        await self._update_plan()

        while self.plan.current_task:
            task = self.plan.current_task
            logger.info(f"ready to take on task {task}")

            # take on current task
            code, result, success = await self._write_and_exec_code()

            # ask for acceptance, users can other refuse and change tasks in the plan
            task_result_confirmed = await self._ask_review()

            if success and task_result_confirmed:
                # tick off this task and record progress
                task.code = code
                task.result = result
                self.plan.finish_current_task()
                self.working_memory.clear()

            else:
                # update plan according to user's feedback and to take on changed tasks
                await self._update_plan()

    async def _write_and_exec_code(self, max_retry: int = 3):
        task_guide = (
            await WriteTaskGuide().run(self.plan.current_task.instruction)
            if self.use_task_guide
            else ""
        )

        counter = 0
        success = False
        while not success and counter < max_retry:
            context = self.get_useful_memories()

            # print("*" * 10)
            # print(context)
            # print("*" * 10)
            # breakpoint()

            if not self.use_tools or self.plan.current_task.task_type == "":
                # code = "print('abc')"
                code = await WriteCodeByGenerate().run(
                    context=context, plan=self.plan, task_guide=task_guide, temperature=0.0
                )
                cause_by = WriteCodeByGenerate
            else:
                code = await WriteCodeWithTools().run(
                    context=context, plan=self.plan, task_guide=task_guide, data_desc=""
                )
                cause_by = WriteCodeWithTools

            self.working_memory.add(
                Message(content=code, role="assistant", cause_by=cause_by)
            )

            result, success = await self.execute_code.run(code)
            # truncated the result
            print(truncate(result))
            # print(result)
            _result = truncate(remove_escape_and_color_codes(result))
            self.working_memory.add(
                Message(content=_result, role="user", cause_by=ExecutePyCode)
            )

            if "!pip" in code:
                success = False
            # if not success:
            #     await self._ask_review()

            counter += 1

        return code, result, success

    async def _ask_review(self):
        if not self.auto_run:
            context = self.get_useful_memories()
            review, confirmed = await AskReview().run(context=context[-5:], plan=self.plan)
            if not confirmed:
                self.working_memory.add(Message(content=review, role="user", cause_by=AskReview))
            return confirmed
        return True

    async def _update_plan(self, max_tasks: int = 3):
        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await WritePlan().run(context, max_tasks=max_tasks)
            self.working_memory.add(
                Message(content=rsp, role="assistant", cause_by=WritePlan)
            )
            plan_confirmed = await self._ask_review()

        tasks = WritePlan.rsp_to_tasks(rsp)
        self.plan.add_tasks(tasks)
        self.working_memory.clear()

    def get_useful_memories(self) -> List[Message]:
        """find useful memories only to reduce context length and improve performance"""

        user_requirement = self.plan.goal
        tasks = json.dumps(
            [task.dict() for task in self.plan.tasks], indent=4, ensure_ascii=False
        )
        current_task = self.plan.current_task.json() if self.plan.current_task else {}
        context = STRUCTURAL_CONTEXT.format(
            user_requirement=user_requirement, tasks=tasks, current_task=current_task
        )
        context_msg = [Message(content=context, role="user")]

        return context_msg + self.working_memory.get()

    @property
    def working_memory(self):
        return self._rc.memory


if __name__ == "__main__":
    requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    # requirement = "Run data analysis on sklearn Diabetes dataset, include a plot"
    # requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy"
    # requirement = "Run data analysis on sklearn Wisconsin Breast Cancer dataset, include a plot, train a model to predict targets (20% as validation), and show validation accuracy"
    # requirement = "Run EDA and visualization on this dataset, train a model to predict survival, report metrics on validation set (20%), dataset: workspace/titanic/train.csv"

    async def main(requirement: str = requirement, auto_run: bool = False):
        role = MLEngineer(goal=requirement, auto_run=auto_run)
        await role.run(requirement)

    fire.Fire(main)
