from __future__ import annotations

import json
import os
from typing import Literal, Union

from pydantic import Field, model_validator

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message, Task, TaskResult
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from user_develop.action.evaluator_report import EvaluatorReport
from user_develop.action.write_analysis_report import WriteAnalysisReport
from user_develop.plan.report_planner import WritePlanner


class RewriteReport(Role):
    name: str = "wangs"
    profile: str = "事故调查报告"
    auto_run: bool = True
    use_plan: bool = True
    planner: WritePlanner = Field(default_factory=WritePlanner)
    evaluator: EvaluatorReport = Field(default_factory=EvaluatorReport, exclude=True)
    use_evaluator: bool = True
    tools: Union[str, list[str]] = []  # Use special symbol ["<all>"] to indicate use of all registered tools
    tool_recommender: ToolRecommender = None
    react_mode: Literal["plan_and_act", "react"] = "plan_and_act"  # "by_order"
    human_design_sop: bool = False
    max_react_loop: int = 5
    use_reflection: bool = False
    upload_file: str = ""

    @model_validator(mode="after")
    def set_plan_and_tool(self):
        self._set_react_mode(react_mode=self.react_mode, max_react_loop=self.max_react_loop, auto_run=self.auto_run)
        # update user_definite planner
        self.planner = WritePlanner(goal=self.goal, working_memory=self.rc.working_memory, auto_run=self.auto_run)
        # Whether to adopt the sop paradigm predefined by humans(是否采用人类预先定义的 sop 范式)
        self.planner.human_design_sop = self.human_design_sop
        self.use_plan = (
            self.react_mode == "plan_and_act"
        )  # create a flag for convenience, overwrite any passed-in value
        if self.tools:
            self.tool_recommender = BM25ToolRecommender(tools=self.tools)
        self.set_actions([WriteAnalysisReport])
        self._set_state(0)
        return self

    @property
    def working_memory(self):
        return self.rc.working_memory

    async def run(self, with_message=None, upload_file="") -> Message | None:
        self.upload_file = upload_file
        await super().run(with_message)

    async def _plan_and_act(self) -> Message:
        rsp = await super()._plan_and_act()
        self.write_out_report()
        return rsp

    async def _act_on_task(self, current_task: Task) -> TaskResult:
        """Useful in 'plan_and_act' mode. Wrap the output in a TaskResult for review and confirmation."""
        code, result, is_success = await self._ready_write_report()
        task_result = TaskResult(code=code, result=result, is_success=is_success)
        return task_result

    async def _ready_write_report(self, max_retry: int = 3):
        counter = 0
        success = False
        plan_status = self.planner.get_plan_status() if self.use_plan else ""

        if self.tools:
            context = (
                self.working_memory.get()[-1].content if self.working_memory.get() else ""
            )  # thoughts from _think stage in 'react' mode
            plan = self.planner.plan if self.use_plan else None
            tool_info = await self.tool_recommender.get_recommended_tool_info(context=context, plan=plan)
        else:
            tool_info = ""
        await self._check_data()
        # 先写报告初稿
        report, cause_by = await self._write_report(counter, plan_status, tool_info)
        self.working_memory.add(Message(content=report, role="assistant", cause_by=cause_by))
        # 对报告初稿进行评估
        if self.use_evaluator:
            success = False
            while not success and counter < max_retry:
                report, result, success = await self.evaluator.run(
                    report=report,
                    user_requirement=self.get_memories()[0].content,
                    plan_status=plan_status,
                    working_memory=self.working_memory.get(),
                )
                self.working_memory.add(Message(content=result, role="user", cause_by=EvaluatorReport))
                counter += 1
        else:
            result, success = "", True
        return report, result, success

    async def _write_report(
        self,
        counter: int,
        plan_status: str = "",
        tool_info: str = "",
    ):
        todo = self.rc.todo  # todo is WriteAnalysisCode
        logger.info(f"ready to {todo.name}")
        use_reflection = counter > 0 and self.use_reflection  # only use reflection after the first trial
        user_requirement = self.get_memories()[0].content
        report = await todo.run(
            user_requirement=user_requirement,
            plan_status=plan_status,
            tool_info=tool_info,
            working_memory=self.working_memory.get(),
            use_reflection=use_reflection,
        )
        return report, todo

    def read_data_info(self):
        # 检查用户是否附带文件信息
        # file_path = DATA_PATH / 'info.json'
        file_path = self.upload_file
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                data_info = json.loads(file.read())
                key = self.planner.current_task.task_type
                data = "\n".join([str(x) for x in data_info[key].items()])
            #   加入业务规则性条件
            if key == "second_paragraph":
                data += "\n".join([str(x) for x in data_info["third_paragraph"].items()])
            self.working_memory.add(Message(content=data, role="user", cause_by="custom"))

    def write_out_report(self):
        # file_path = DATA_PATH / 'report.txt'
        directory, _ = os.path.splitext(self.upload_file)
        file_path = f"{directory}_metagpt.txt"
        result = ""
        for task in self.planner.plan.tasks:
            result += f"{task.code}\n"
        with open(file_path, "w") as f:
            f.write(result)

    async def _check_data(self):
        if "custom" not in self.working_memory.index:
            logger.info("add user additional data into working_memory")
            self.read_data_info()
        if not self.use_plan or not self.planner.plan.get_finished_tasks() or self.planner.plan.current_task.task_type:
            return
