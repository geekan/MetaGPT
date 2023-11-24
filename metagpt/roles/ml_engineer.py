from typing import Dict, List, Union
import json
import subprocess

import fire

from metagpt.roles import Role
from metagpt.actions import Action
from metagpt.schema import Message, Task, Plan
from metagpt.logs import logger
from metagpt.actions.write_plan import WritePlan
from metagpt.actions.write_code_function import WriteCodeFunction
from metagpt.actions.execute_code import ExecutePyCode

class AskReview(Action):

    async def run(self, context: List[Message], plan: Plan = None):
        prompt = "\n".join(
            [f"{msg.cause_by() if msg.cause_by else 'Main Requirement'}: {msg.content}" for msg in context]
        )

        latest_action = context[-1].cause_by()

        prompt += f"\nPlease review output from {latest_action}, " \
            "provide feedback or type YES to continue with the process:\n"
        rsp = input(prompt)
        confirmed = "yes" in rsp.lower()
        return rsp, confirmed


class MLEngineer(Role):
    def __init__(self, name="ABC", profile="MLEngineer"):
        super().__init__(name=name, profile=profile)
        self._set_react_mode(react_mode="plan_and_act")
        self.plan = Plan()

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
        counter = 0
        success = False
        while not success and counter < max_retry:
            context = self.get_memories()
            print(f"{'*'*20}\n {context}")
            # code = "print('abc')"
            code = await WriteCodeFunction().run(context=context)
            # code = await WriteCodeWithOps.run(context, task, result)
            self._rc.memory.add(Message(content=code, role="assistant", cause_by=WriteCodeFunction))

            result, success = await ExecutePyCode().run(code)
            self._rc.memory.add(Message(content=result, role="user", cause_by=ExecutePyCode))

            # if not success:
            #     await self._ask_review()

            counter += 1

        return code, result, success

    async def _ask_review(self):
        context = self.get_memories()
        review, confirmed = await AskReview().run(context=context[-5:], plan=self.plan)
        self._rc.memory.add(Message(content=review, role="user", cause_by=AskReview))
        return confirmed

    async def _update_plan(self, max_tasks: int = 3):
        current_plan = str([task.json() for task in self.plan.tasks])
        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_memories()
            rsp = await WritePlan().run(context, current_plan=current_plan, max_tasks=max_tasks)
            self._rc.memory.add(Message(content=rsp, role="assistant", cause_by=WritePlan))
            plan_confirmed = await self._ask_review()

        tasks = WritePlan.rsp_to_tasks(rsp)
        self.plan.add_tasks(tasks)


if __name__ == "__main__":
    # requirement = "create a normal distribution and visualize it"
    requirement = "run some analysis on iris dataset"

    async def main(requirement: str = requirement):
        role = MLEngineer()
        await role.run(requirement)

    fire.Fire(main)
