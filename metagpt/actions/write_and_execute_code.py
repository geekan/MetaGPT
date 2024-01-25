from pydantic import Field

from metagpt.actions.ask_review import ReviewConst
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools
from metagpt.logs import logger
from metagpt.plan.planner import Planner
from metagpt.plan.schema import Plan, TaskAction
from metagpt.schema import Message


class WriteAndExecuteCode(TaskAction):
    name: str = "WriteAndExecuteCode"
    desc: str = "For writing and executing codes to solve a task"
    code_steps: str = ""
    code: str = ""
    use_tools: bool = False
    tools: list[str] = []
    execute_code: ExecutePyCode = Field(exclude=True)

    async def run(self, context: list[Message], planner: Planner, max_retry: int = 3):
        plan = planner.plan
        working_memory = planner.working_memory

        counter = 0
        success = False

        while not success and counter < max_retry:
            ### write code ###
            code, cause_by = await self._write_code(context=context, plan=plan)

            working_memory.add(Message(content=code["code"], role="assistant", cause_by=cause_by))

            ### execute code ###
            result, success = await self.execute_code.run(**code)
            print(result)

            working_memory.add(Message(content=result, role="user", cause_by=ExecutePyCode))

            ### process execution result ###
            if "!pip" in code["code"]:
                success = False

            counter += 1

            if not success and counter >= max_retry:
                logger.info("coding failed!")
                review, _ = await planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORD[0] in review:
                    counter = 0  # redo the task again with help of human suggestions

        self.code = code["code"]
        self.result = result
        self.is_success = success
        return result

    async def _write_code(self, context: list[Message], plan: Plan):
        todo = WriteCodeByGenerate() if not self.use_tools else WriteCodeWithTools(selected_tools=self.tools)
        logger.info(f"ready to {todo.name}")

        code = await todo.run(context=context, plan=plan, temperature=0.0)

        return code, todo
