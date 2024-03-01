from __future__ import annotations

from pydantic import Field

from metagpt.actions.di.ask_review import ReviewConst
from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from metagpt.actions.di.write_analysis_code import (
    WriteCodeWithoutTools,
    WriteCodeWithTools,
)
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message, Task, TaskResult


class DataInterpreter(Role):
    name: str = "David"
    profile: str = "DataInterpreter"
    auto_run: bool = True
    use_tools: bool = False
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

        while not success and counter < max_retry:
            ### write code ###
            code, cause_by = await self._write_code()

            self.working_memory.add(Message(content=code["code"], role="assistant", cause_by=cause_by))

            ### execute code ###
            result, success = await self.execute_code.run(**code)
            print(result)

            self.working_memory.add(Message(content=result, role="user", cause_by=ExecuteNbCode))

            ### process execution result ###
            counter += 1

            if not success and counter >= max_retry:
                logger.info("coding failed!")
                review, _ = await self.planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORDS[0] in review:
                    counter = 0  # redo the task again with help of human suggestions

        return code["code"], result, success

    async def _write_code(self):
        todo = WriteCodeWithoutTools() if not self.use_tools else WriteCodeWithTools(selected_tools=self.tools)
        logger.info(f"ready to {todo.name}")

        context = self.planner.get_useful_memories()
        # print(*context, sep="\n***\n")
        code = await todo.run(context=context, plan=self.planner.plan, temperature=0.0)

        return code, todo
