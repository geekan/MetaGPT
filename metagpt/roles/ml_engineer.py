from typing import Dict, List, Union
import json
import subprocess

import fire

from metagpt.roles import Role
from metagpt.actions import Action
from metagpt.schema import Message, Task, Plan
from metagpt.logs import logger
from metagpt.actions.write_plan import WritePlan
from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools
from metagpt.actions.execute_code import ExecutePyCode

class AskReview(Action):

    async def run(self, context: List[Message], plan: Plan = None):
        logger.info("Current overall plan:")
        logger.info("\n".join([f"{task.task_id}: {task.instruction}" for task in plan.tasks]))

        logger.info("most recent context:")
        # prompt = "\n".join(
        #     [f"{msg.cause_by.__name__ if msg.cause_by else 'Main Requirement'}: {msg.content}" for msg in context]
        # )
        prompt = ""
        latest_action = context[-1].cause_by.__name__
        prompt += f"\nPlease review output from {latest_action}:\n" \
            "If you want to change a task in the plan, say 'change task task_id, ... (things to change)'\n" \
            "If you confirm the output and wish to continue with the current process, type CONFIRM:\n"
        rsp = input(prompt)
        confirmed = "confirm" in rsp.lower()

        return rsp, confirmed

class WriteTaskGuide(Action):

    async def run(self, task_instruction: str, data_desc: str = "") -> str:
        return ""

class MLEngineer(Role):
    def __init__(self, name="ABC", profile="MLEngineer", goal=""):
        super().__init__(name=name, profile=profile, goal=goal)
        self._set_react_mode(react_mode="plan_and_act")
        self.plan = Plan(goal=goal)
        self.use_tools = False
        self.use_task_guide = False

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

            else:
                # update plan according to user's feedback and to take on changed tasks
                await self._update_plan()

    async def _write_and_exec_code(self, max_retry: int = 3):

        task_guide = await WriteTaskGuide().run(self.plan.current_task.instruction) if self.use_task_guide else ""

        counter = 0
        success = False
        while not success and counter < max_retry:
            context = self.get_useful_memories()

            if not self.use_tools:
                # code = "print('abc')"
                code = await WriteCodeByGenerate().run(context=context, plan=self.plan, task_guide=task_guide)
                cause_by = WriteCodeByGenerate

            else:
                code = await WriteCodeWithTools().run(context=context, plan=self.plan, task_guide=task_guide)
                cause_by = WriteCodeWithTools

            self._rc.memory.add(Message(content=code, role="assistant", cause_by=cause_by))

            result, success = await ExecutePyCode().run(code)
            print(result)
            self._rc.memory.add(Message(content=result, role="user", cause_by=ExecutePyCode))

            # if not success:
            #     await self._ask_review()

            counter += 1

        return code, result, success

    async def _ask_review(self):
        context = self.get_useful_memories()
        review, confirmed = await AskReview().run(context=context[-5:], plan=self.plan)
        self._rc.memory.add(Message(content=review, role="user", cause_by=AskReview))
        return confirmed

    async def _update_plan(self, max_tasks: int = 3):
        current_plan = str([task.json() for task in self.plan.tasks])
        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await WritePlan().run(context, current_plan=current_plan, max_tasks=max_tasks)
            self._rc.memory.add(Message(content=rsp, role="assistant", cause_by=WritePlan))
            plan_confirmed = await self._ask_review()

        tasks = WritePlan.rsp_to_tasks(rsp)
        self.plan.add_tasks(tasks)

    def get_useful_memories(self, current_task_memories: List[str] = []) -> List[Message]:
        """find useful memories only to reduce context length and improve performance"""
        memories = super().get_memories()
        return memories


if __name__ == "__main__":
    # requirement = "create a normal distribution and visualize it"
    requirement = "run some analysis on iris dataset"

    async def main(requirement: str = requirement):
        role = MLEngineer(goal=requirement)
        await role.run(requirement)

    fire.Fire(main)
