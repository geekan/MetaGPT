from __future__ import annotations

from pydantic import Field

from metagpt.actions.mi.ask_review import ReviewConst
from metagpt.actions.mi.execute_nb_code import ExecuteNbCode
from metagpt.actions.mi.write_analysis_code import CheckData, WriteCodeWithTools
from metagpt.logs import logger
from metagpt.prompts.mi.write_analysis_code import DATA_INFO
from metagpt.roles import Role
from metagpt.schema import Message, Task, TaskResult
from metagpt.tools.tool_type import ToolType


class Interpreter(Role):
    name: str = "Ivy"
    profile: str = "Interpreter"
    auto_run: bool = True
    use_tools: bool = False
    use_reflection: bool = False
    execute_code: ExecuteNbCode = Field(default_factory=ExecuteNbCode, exclude=True)
    tools: list[str] = []

    def __init__(
        self,
        auto_run=True,
        use_tools=False,
        tools=[],
        **kwargs,
    ):
        super().__init__(auto_run=auto_run, use_tools=use_tools, tools=tools, **kwargs)
        self._set_react_mode(react_mode="plan_and_act", auto_run=auto_run, use_tools=use_tools)
        if use_tools and tools:
            from metagpt.tools.tool_registry import (
                validate_tool_names,  # import upon use
            )

            self.tools = validate_tool_names(tools)
            logger.info(f"will only use {self.tools} as tools")

    @property
    def working_memory(self):
        return self.rc.working_memory

    async def _act_on_task(self, current_task: Task) -> TaskResult:
        code, result, is_success = await self._write_and_exec_code()
        task_result = TaskResult(code=code, result=result, is_success=is_success)
        return task_result

    async def _write_and_exec_code(self, max_retry: int = 3):
        counter = 0
        success = False

        await self._check_data()

        while not success and counter < max_retry:
            ### write code ###
            code, cause_by = await self._write_code(counter)

            self.working_memory.add(Message(content=code, role="assistant", cause_by=cause_by))

            ### execute code ###
            result, success = await self.execute_code.run(code)
            print(result)

            self.working_memory.add(Message(content=result, role="user", cause_by=ExecuteNbCode))

            ### process execution result ###
            counter += 1

            if not success and counter >= max_retry:
                logger.info("coding failed!")
                review, _ = await self.planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORDS[0] in review:
                    counter = 0  # redo the task again with help of human suggestions

        return code, result, success

    async def _write_code(self, counter):
        todo = WriteCodeWithTools(use_tools=self.use_tools, selected_tools=self.tools)
        logger.info(f"ready to {todo.name}")
        use_reflection = counter > 0 and self.use_reflection
        code = await todo.run(
            plan=self.planner.plan, working_memory=self.working_memory.get(), use_reflection=use_reflection
        )

        return code, todo

    async def _check_data(self):
        current_task = self.planner.plan.current_task
        if current_task.task_type not in [
            ToolType.DATA_PREPROCESS.type_name,
            ToolType.FEATURE_ENGINEERING.type_name,
            ToolType.MODEL_TRAIN.type_name,
        ]:
            return
        logger.info("Check updated data")
        code = await CheckData().run(self.planner.plan)
        if not code.strip():
            return
        success = False
        result, success = await self.execute_code.run(code)
        if success:
            print(result)
            data_info = DATA_INFO.format(info=result)
            self.working_memory.add(Message(content=data_info, role="user", cause_by=CheckData))
