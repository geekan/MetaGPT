from typing import Dict, List, Union
import json
import subprocess

import fire
import re

from metagpt.roles import Role
from metagpt.actions import Action
from metagpt.schema import Message, Task, Plan
from metagpt.memory import Memory
from metagpt.logs import logger
from metagpt.actions.write_plan import WritePlan, update_plan_from_rsp, precheck_update_plan_from_rsp
from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools
from metagpt.actions.ml_da_action import AskReview, SummarizeAnalysis, Reflect, ReviewConst
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.roles.kaggle_manager import DownloadData, SubmitResult
from metagpt.prompts.ml_engineer import STRUCTURAL_CONTEXT
from metagpt.actions.write_code_steps import WriteCodeSteps

class MLEngineer(Role):
    def __init__(
        self, name="ABC", profile="MLEngineer", goal="", auto_run: bool = False
    ):
        super().__init__(name=name, profile=profile, goal=goal)
        self._set_react_mode(react_mode="plan_and_act")
        self._watch([DownloadData, SubmitResult])

        self.plan = Plan(goal=goal)
        self.use_tools = False
        self.use_code_steps = True
        self.execute_code = ExecutePyCode()
        self.auto_run = auto_run

        # memory for working on each task, discarded each time a task is done
        self.working_memory = Memory()

    async def _plan_and_act(self):

        ### Actions in a multi-agent multi-turn setting ###
        memories = self.get_memories()
        if memories:
            latest_event = memories[-1].cause_by
            if latest_event == DownloadData:
                self.plan.context = memories[-1].content
            elif latest_event == SubmitResult:
                # self reflect on previous plan outcomes and think about how to improve the plan, add to working  memory
                await self._reflect()

                # get feedback for improvement from human, add to working memory
                await self._ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)

        ### Common Procedure in both single- and multi-agent setting ###
        # create initial plan and update until confirmation
        await self._update_plan()

        while self.plan.current_task:
            task = self.plan.current_task
            logger.info(f"ready to take on task {task}")

            # take on current task
            code, result, success, code_steps = await self._write_and_exec_code()

            # ask for acceptance, users can other refuse and change tasks in the plan
            review, task_result_confirmed = await self._ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)

            if task_result_confirmed:
                # tick off this task and record progress
                task.code = code
                task.result = result
                task.code_steps = code_steps
                self.plan.finish_current_task()
                self.working_memory.clear()

                confirmed_and_more = (ReviewConst.CONTINUE_WORD[0] in review.lower()
                    and review.lower() not in ReviewConst.CONTINUE_WORD[0])  # "confirm, ... (more content, such as changing downstream tasks)"
                if confirmed_and_more:
                    self.working_memory.add(Message(content=review, role="user", cause_by=AskReview))
                    await self._update_plan(review)
            
            elif "redo" in review:
                # Ask the Role to redo this task with help of review feedback,
                # useful when the code run is successful but the procedure or result is not what we want
                continue

            else:
                # update plan according to user's feedback and to take on changed tasks
                await self._update_plan(review)

        completed_plan_memory = self.get_useful_memories()  # completed plan as a outcome
        self._rc.memory.add(completed_plan_memory[0])  # add to persistent memory

        summary = await SummarizeAnalysis().run(self.plan)
        rsp = Message(content=summary, cause_by=SummarizeAnalysis)
        self._rc.memory.add(rsp)

        return rsp

    async def _write_and_exec_code(self, max_retry: int = 3):
        code_steps = (
            await WriteCodeSteps().run(self.plan)
            if self.use_code_steps
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

            if not self.use_tools or self.plan.current_task.task_type == "other":
                # code = "print('abc')"
                code = await WriteCodeByGenerate().run(
                    context=context, plan=self.plan, code_steps=code_steps, temperature=0.0
                )
                cause_by = WriteCodeByGenerate
            else:
                code = await WriteCodeWithTools().run(
                    context=context, plan=self.plan, code_steps=code_steps, data_desc=""
                )
                cause_by = WriteCodeWithTools

            self.working_memory.add(
                Message(content=code, role="assistant", cause_by=cause_by)
            )

            result, success = await self.execute_code.run(code)
            print(result)
            self.working_memory.add(
                Message(content=result, role="user", cause_by=ExecutePyCode)
            )

            if "!pip" in code:
                success = False

            counter += 1

            if not success and counter >= max_retry:
                logger.info("coding failed!")
                review, _ = await self._ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORD in review:
                    counter = 0  # redo the task again with help of human suggestions

        return code, result, success, code_steps

    async def _ask_review(self, auto_run: bool = None, trigger: str = ReviewConst.TASK_REVIEW_TRIGGER):
        auto_run = auto_run or self.auto_run
        if not auto_run:
            context = self.get_useful_memories()
            review, confirmed = await AskReview().run(context=context[-5:], plan=self.plan, trigger=trigger)
            if not confirmed:
                self.working_memory.add(Message(content=review, role="user", cause_by=AskReview))
            return review, confirmed
        return "", True

    async def _update_plan(self, review: str = "", max_tasks: int = 3, max_retries: int = 3):
        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await WritePlan().run(
                context, max_tasks=max_tasks, use_tools=self.use_tools
            )
            self.working_memory.add(
                Message(content=rsp, role="assistant", cause_by=WritePlan)
            )

            # precheck plan before asking reviews
            is_plan_valid, error = precheck_update_plan_from_rsp(rsp, self.plan)
            if not is_plan_valid and max_retries > 0:
                error_msg = f"The generated plan is not valid with error: {error}, try regenerating, remember to generate either the whole plan or the single changed task only"
                logger.warning(error_msg)
                self.working_memory.add(Message(content=error_msg, role="assistant", cause_by=WritePlan))
                max_retries -= 1
                continue

            _, plan_confirmed = await self._ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)

        update_plan_from_rsp(rsp, self.plan)

        self.working_memory.clear()
    
    async def _reflect(self):
        context = self.get_memories()
        context = "\n".join([str(msg) for msg in context])
        # print("*" * 10)
        # print(context)
        # print("*" * 10)
        reflection = await Reflect().run(context=context)
        self.working_memory.add(Message(content=reflection, role="assistant"))
        self.working_memory.add(Message(content=Reflect.REWRITE_PLAN_INSTRUCTION, role="user"))

    def get_useful_memories(self) -> List[Message]:
        """find useful memories only to reduce context length and improve performance"""
        # TODO dataset description , code steps
        user_requirement = self.plan.goal
        data_desc = self.plan.context
        tasks = json.dumps(
            [task.dict() for task in self.plan.tasks], indent=4, ensure_ascii=False
        )
        current_task = self.plan.current_task.json() if self.plan.current_task else {}
        context = STRUCTURAL_CONTEXT.format(
            user_requirement=user_requirement, data_desc=data_desc, tasks=tasks, current_task=current_task
        )
        context_msg = [Message(content=context, role="user")]

        return context_msg + self.get_working_memories()
    
    def get_working_memories(self) -> List[Message]:
        return self.working_memory.get()


if __name__ == "__main__":
    # requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    # requirement = "Run data analysis on sklearn Diabetes dataset, include a plot"
    # requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy"
    # requirement = "Run data analysis on sklearn Wisconsin Breast Cancer dataset, include a plot, train a model to predict targets (20% as validation), and show validation accuracy"
    requirement = "Run EDA and visualization on this dataset, train a model to predict survival, report metrics on validation set (20%), dataset: workspace/titanic/train.csv"

    async def main(requirement: str = requirement, auto_run: bool = False):
        role = MLEngineer(goal=requirement, auto_run=auto_run)
        await role.run(requirement)

    fire.Fire(main)
