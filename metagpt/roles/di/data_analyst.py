from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.actions.di.write_analysis_code import CheckData, WriteAnalysisCode
from metagpt.logs import logger
from metagpt.prompts.di.data_analyst import (
    CODE_STATUS,
    EXTRA_INSTRUCTION,
    TASK_TYPE_DESC,
)
from metagpt.prompts.di.role_zero import ROLE_INSTRUCTION
from metagpt.prompts.di.write_analysis_code import DATA_INFO
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message, TaskResult
from metagpt.strategy.experience_retriever import ExpRetriever, KeywordExpRetriever
from metagpt.strategy.task_type import TaskType
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.tools.tool_registry import register_tool


@register_tool(include_functions=["write_and_exec_code"])
class DataAnalyst(RoleZero):
    name: str = "David"
    profile: str = "DataAnalyst"
    goal: str = "Take on any data-related tasks, such as data analysis, machine learning, deep learning, web browsing, web scraping, web searching, terminal operation, document QA & analysis, etc."
    instruction: str = ROLE_INSTRUCTION + EXTRA_INSTRUCTION
    task_type_desc: str = TASK_TYPE_DESC

    tools: list[str] = [
        "Plan",
        "DataAnalyst",
        "RoleZero",
        "Browser",
        "Editor:write,read,similarity_search",
        "SearchEnhancedQA",
    ]
    custom_tools: list[str] = ["web scraping", "Terminal", "Editor:write,read,similarity_search"]
    custom_tool_recommender: ToolRecommender = None
    experience_retriever: Annotated[ExpRetriever, Field(exclude=True)] = KeywordExpRetriever()

    use_reflection: bool = True
    write_code: WriteAnalysisCode = Field(default_factory=WriteAnalysisCode, exclude=True)
    execute_code: ExecuteNbCode = Field(default_factory=ExecuteNbCode, exclude=True)

    @model_validator(mode="after")
    def set_custom_tool(self):
        if self.custom_tools and not self.custom_tool_recommender:
            self.custom_tool_recommender = BM25ToolRecommender(tools=self.custom_tools, force=True)

    def _update_tool_execution(self):
        self.tool_execution_map.update(
            {
                "DataAnalyst.write_and_exec_code": self.write_and_exec_code,
            }
        )

    async def write_and_exec_code(self, instruction: str = ""):
        """Write a code block for current task and execute it in an interactive notebook environment.

        Args:
            instruction (optional, str): Further hints or notice other than the current task instruction, must be very concise and can be empty. Defaults to "".
        """
        if self.planner.plan:
            logger.info(f"Current task {self.planner.plan.current_task}")

        counter = 0
        success = False
        await self.execute_code.init_code()

        # plan info
        if self.planner.current_task:
            # clear task result from plan to save token, since it has been in memory
            plan_status = self.planner.get_plan_status(exclude=["task_result"])
            plan_status += f"\nFurther Task Instruction: {instruction}"
        else:
            return "No current_task found now. Please use command Plan.append_task to add a task first."

        # tool info
        if self.custom_tool_recommender:
            plan = self.planner.plan
            fixed = ["Terminal"] if "Terminal" in self.custom_tools else None
            tool_info = await self.custom_tool_recommender.get_recommended_tool_info(fixed=fixed, plan=plan)
        else:
            tool_info = ""

        # data info
        await self._check_data()

        while not success and counter < 3:
            ### write code ###
            logger.info("ready to WriteAnalysisCode")
            use_reflection = counter > 0 and self.use_reflection  # only use reflection after the first trial

            code = await self.write_code.run(
                user_requirement=self.planner.plan.goal,
                plan_status=plan_status,
                tool_info=tool_info,
                working_memory=self.rc.working_memory.get(),
                use_reflection=use_reflection,
                memory=self.rc.memory.get(self.memory_k),
            )
            self.rc.working_memory.add(Message(content=code, role="assistant", cause_by=WriteAnalysisCode))

            ### execute code ###
            result, success = await self.execute_code.run(code)
            print(result)

            self.rc.working_memory.add(Message(content=result, role="user", cause_by=ExecuteNbCode))

            ### process execution result ###
            counter += 1
            if success:
                task_result = TaskResult(code=code, result=result, is_success=success)
                self.planner.current_task.update_task_result(task_result)

        status = "Success" if success else "Failed"
        output = CODE_STATUS.format(code=code, status=status, result=result)
        if success:
            output += "The code written has been executed successfully."
        self.rc.working_memory.clear()
        return output

    async def _check_data(self):
        if not self.planner.plan.get_finished_tasks() or self.planner.plan.current_task.task_type not in [
            TaskType.DATA_PREPROCESS.type_name,
            TaskType.FEATURE_ENGINEERING.type_name,
            TaskType.MODEL_TRAIN.type_name,
        ]:
            return
        logger.info("Check updated data")
        code = await CheckData().run(self.planner.plan)
        if not code.strip():
            return
        result, success = await self.execute_code.run(code)
        if success:
            print(result)
            data_info = DATA_INFO.format(info=result)
            self.rc.working_memory.add(Message(content=data_info, role="user", cause_by=CheckData))

    async def _run_special_command(self, cmd) -> str:
        """command requiring special check or parsing."""
        # TODO: duplicate with Engineer2._run_special_command, consider dedup

        # finish current task before end.
        command_output = ""
        if cmd["command_name"] == "end" and not self.planner.plan.is_plan_finished():
            self.planner.plan.finish_all_tasks()
            command_output += "All tasks are finished.\n"
        command_output += await super()._run_special_command(cmd)
        return command_output
