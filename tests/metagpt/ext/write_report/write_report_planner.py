from __future__ import annotations

import json

import yaml

from metagpt.actions.di.ask_review import ReviewConst

# from user_develop.prompt.report_task_type import UserTaskType
from metagpt.actions.di.write_plan import (
    WritePlan,
    precheck_update_plan_from_rsp,
    update_plan_from_rsp,
)
from metagpt.const import TEST_DATA_PATH
from metagpt.logs import logger
from metagpt.schema import Message, Plan
from metagpt.strategy.planner import Planner
from metagpt.utils.common import CodeParser, remove_comments

PLAN_STATUS = """
当前任务：{current_task}

已生成的章节段落：
{report_written}

为了更好地协助您完成任务，以下是一些指导性建议:
{guidance}

"""
#  Prompt for loading chapters or paragraph
with open(TEST_DATA_PATH / "report_writer/domain.yaml", "r") as file:
    usertasktype = yaml.safe_load(file)
guidances = {v["name"]: v["guidance"] for k, v in usertasktype.items()}


class WriteReportPlan(WritePlan):
    CONSTRAINTS: str = """
    # Constraints
       -  Arrange the plan strictly in paragraph order.
       -  Cannot arrange the same paragraph repeatedly
    """

    async def run(self, context: list[Message], max_tasks: int = 7, human_design_sop=True) -> str:
        if not human_design_sop:
            self.PROMPT_TEMPLATE = f"{self.PROMPT_TEMPLATE}\n\n{self.CONSTRAINTS}"
            task_type_desc = "\n".join([f"- **{v['name']}**: {v['desc']}" for k, v in usertasktype.items()])
            prompt = self.PROMPT_TEMPLATE.format(
                context="\n".join([str(ct) for ct in context]), max_tasks=max_tasks, task_type_desc=task_type_desc
            )
            rsp = await self._aask(prompt)
            rsp = CodeParser.parse_code(block=None, text=rsp)
        else:
            with open(TEST_DATA_PATH / "report_writer/sop.json", "r", encoding="utf-8") as file:
                rsp = json.dumps(json.loads(file.read()), ensure_ascii=False)  # 读取人类设计 `sop` 流程
        return rsp


class WriteReportPlanner(Planner):
    human_design_sop: bool = False

    async def update_plan(self, goal: str = "", max_tasks: int = 7, max_retries: int = 3):
        if goal:
            self.plan = Plan(goal=goal)
        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await WriteReportPlan().run(context, max_tasks, self.human_design_sop)
            self.working_memory.add(Message(content=rsp, role="assistant", cause_by=WritePlan))
            # precheck plan before asking reviews
            is_plan_valid, error = precheck_update_plan_from_rsp(rsp, self.plan)
            if not is_plan_valid and max_retries > 0:
                error_msg = f"The generated plan is not valid with error: {error}, try regenerating, remember to generate either the whole plan or the single changed task only"
                logger.warning(error_msg)
                self.working_memory.add(Message(content=error_msg, role="assistant", cause_by=WritePlan))
                max_retries -= 1
                continue
            _, plan_confirmed = await self.ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)
        update_plan_from_rsp(rsp=rsp, current_plan=self.plan)
        # working_memory
        self.working_memory.clear()

    def get_plan_status(self) -> str:
        # prepare components of a plan status
        finished_tasks = self.plan.get_finished_tasks()
        paragraph_written = [remove_comments(task.code) for task in finished_tasks]
        paragraph_written = "\n\n".join(paragraph_written)
        task_results = [task.result for task in finished_tasks]
        task_results = "\n\n".join(task_results)
        task_type_name = self.current_task.task_type.lower()
        guidance = guidances.get(task_type_name, "")
        # combine components in a prompt
        prompt = PLAN_STATUS.format(
            report_written=paragraph_written,
            validate_result=task_results,
            current_task=self.current_task.instruction,
            guidance=guidance,
        )
        return prompt
