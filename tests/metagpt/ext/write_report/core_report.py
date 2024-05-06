from __future__ import annotations

import json
import os
from typing import Literal, Union

from pydantic import Field, model_validator

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message, Task, TaskResult
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from tests.metagpt.ext.write_report.write_evaluator_refine import (
    EvaluatorReport,
    RefineReport,
    WriteAnalysisReport,
)
from tests.metagpt.ext.write_report.write_report_planner import WritePlanner


class RewriteReport(Role):
    name: str = "wangs"
    profile: str = "事故调查报告"
    auto_run: bool = True
    use_plan: bool = True
    planner: WritePlanner = Field(default_factory=WritePlanner)
    evaluator: EvaluatorReport = Field(default_factory=EvaluatorReport, exclude=True)
    refine: RefineReport = Field(default_factory=RefineReport, exclude=True)

    use_evaluator: bool = True
    tools: Union[str, list[str]] = []  # Use special symbol ["<all>"] to indicate use of all registered tools
    tool_recommender: ToolRecommender = ToolRecommender()
    react_mode: Literal["plan_and_act", "react"] = "plan_and_act"  # "by_order"
    human_design_sop: bool = False
    max_react_loop: int = 5
    use_reflection: bool = False

    # 重构
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

    # 重构
    async def run(self, with_message=None, upload_file="") -> Message | None:
        """
        Asynchronously runs the function.

        Args:
            with_message (Any, optional): The message to be passed to the superclass run method. Defaults to None.
            upload_file (str, optional): The file to be uploaded. Defaults to "".

        Raises:
            ValueError: If the upload_file does not exist.

        Returns:
            Message | None: The result of the superclass run method.
        """
        if not os.path.exists(upload_file):
            raise ValueError("upload_file must be provided")
        self.upload_file = upload_file
        return await super().run(with_message)

    # 重构
    async def _plan_and_act(self) -> Message:
        rsp = await super()._plan_and_act()
        self.write_out_report()
        return rsp

    async def _act_on_task(self, current_task: Task) -> TaskResult:
        code, result, is_success = await self._ready_write_report()
        task_result = TaskResult(code=code, result=result, is_success=is_success)
        return task_result

    async def _ready_write_report(self, max_retry: int = 3):
        """
        Asynchronously prepares the report for writing.

        Args:
            max_retry (int, optional): The maximum number of retries for evaluating the report. Defaults to 3.

        Returns:
            Tuple[str, str, bool]: A tuple containing the report, suggestion, and success status.
                - report (str): The generated report.
                - suggestion (str): The suggestion for improving the report.
                - success (bool): Indicates whether the report evaluation was successful.

        Raises:
            AttributeError: If the planner is not initialized and use_plan is True.

        """
        if self.use_plan:
            if self.planner is None:
                raise AttributeError("Planner is not initialized")
            plan_status = self.planner.get_plan_status()
        else:
            plan_status = ""

        if self.tools:
            context = self.working_memory.get()[-1].content if self.working_memory.get() else ""
            plan = self.planner.plan if self.use_plan else None
            tool_info = await self.tool_recommender.get_recommended_tool_info(context=context, plan=plan)
        else:
            tool_info = ""

        await self._check_data()
        # Write the first draft of the report first
        report, cause_by = await self._write_report(plan_status, tool_info)
        self.working_memory.add(Message(content=report, role="assistant", cause_by=cause_by))
        suggestion, success = "", True
        # Evaluate the first draft of the report
        if self.use_evaluator:
            counter = 0
            success = False
            while not success and counter < max_retry:
                suggestion, success = await self.evaluator.run(working_memory=self.working_memory.get())
                # Unsuccessful evaluation, manuscript improvement
                if not success:
                    report = await self.refine.run(suggestion=suggestion, working_memory=self.working_memory.get())
                    # Update working_memory to replace the first draft with the reviewed manuscript
                    self.working_memory.delete(self.working_memory.get()[-1])
                    self.working_memory.add(Message(content=report, role="assistant", cause_by=RefineReport))
                else:
                    break
                counter += 1
        return report, suggestion, success

    async def _write_report(
        self,
        plan_status: str = "",
        tool_info: str = "",
    ):
        if not hasattr(self, "rc") or not hasattr(self.rc, "todo"):
            raise AttributeError("Expected 'rc' and 'rc.todo' to be initialized")
        todo = self.rc.todo  # todo is WriteAnalysisCode
        logger.info(f"ready to {todo.name}")
        user_requirement = self.get_memories()[0].content
        structual_prompt, report = await todo.run(
            user_requirement=user_requirement,
            plan_status=plan_status,
            tool_info=tool_info,
            working_memory=self.working_memory.get(),
        )
        # Initially, the file information attached to the user is loaded into working_memory. Now we are trying to update it so that working_memory only retains questions and answers (user/assistant).
        if self.working_memory and self.working_memory.get()[-1].cause_by == "custom":
            self.working_memory.delete(self.working_memory.get()[-1])
            self.working_memory.add(Message(content=structual_prompt, role="user", cause_by=RewriteReport))
        return report, todo

    def read_data_info(self):
        file_path = self.upload_file
        with open(file_path, "r", encoding="utf-8") as file:
            data_info = json.loads(file.read())
            key = self.planner.current_task.task_type
            data = "\n".join([str(x) for x in data_info[key].items()])
        #   Add rule conditions
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
        if self.working_memory.index is None or "custom" not in self.working_memory.index:
            logger.info("add user additional data into working_memory")
            self.read_data_info()
        if not self.use_plan or not self.planner.plan.get_finished_tasks() or self.planner.plan.current_task.task_type:
            return
