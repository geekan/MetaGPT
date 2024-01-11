from datetime import datetime

from pydantic import Field

from metagpt.actions.ask_review import ReviewConst
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.roles.tool_maker import ToolMaker
from metagpt.schema import Message, Task, TaskResult
from metagpt.utils.save_code import save_code_file


class CodeInterpreter(Role):
    auto_run: bool = True
    use_tools: bool = False
    make_udfs: bool = False  # whether to save user-defined functions
    execute_code: ExecutePyCode = Field(default_factory=ExecutePyCode, exclude=True)

    def __init__(
        self,
        name="Charlie",
        profile="CodeInterpreter",
        goal="",
        auto_run=True,
        use_tools=False,
        make_udfs=False,
        **kwargs,
    ):
        super().__init__(
            name=name, profile=profile, goal=goal, auto_run=auto_run, use_tools=use_tools, make_udfs=make_udfs, **kwargs
        )
        self._set_react_mode(react_mode="plan_and_act", auto_run=auto_run, use_tools=use_tools)

    @property
    def working_memory(self):
        return self.rc.working_memory

    async def _plan_and_act(self):
        rsp = await super()._plan_and_act()

        # save code using datetime.now or keywords related to the goal of your project (plan.goal).
        project_record = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_code_file(name=project_record, code_context=self.execute_code.nb, file_format="ipynb")

        # make tools out of workable codes for future use
        if self.make_udfs:
            await self.make_tools()

        return rsp

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

            self.working_memory.add(Message(content=code, role="assistant", cause_by=cause_by))

            ### execute code ###
            result, success = await self.execute_code.run(code)
            print(result)

            self.working_memory.add(Message(content=result, role="user", cause_by=ExecutePyCode))

            ### process execution result ###
            if "!pip" in code:
                success = False

            counter += 1

            if not success and counter >= max_retry:
                logger.info("coding failed!")
                review, _ = await self.planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORD[0] in review:
                    counter = 0  # redo the task again with help of human suggestions

        return code, result, success

    async def _write_code(self):
        todo = WriteCodeByGenerate() if not self.use_tools else WriteCodeWithTools()
        logger.info(f"ready to {todo.name}")

        context = self.planner.get_useful_memories()
        code = await todo.run(context=context, plan=self.planner.plan, temperature=0.0)

        return code, todo

    async def make_tools(self):
        """Make user-defined functions(udfs, aka tools) for pure generation code."""
        logger.info("Plan completed. Now start to make tools ...")
        tool_maker = ToolMaker()
        for task in self.planner.plan.get_finished_tasks():
            await tool_maker.make_tool(
                code=task.code, instruction=task.instruction, task_id=task.task_id, auto_run=self.auto_run
            )
