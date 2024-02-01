from metagpt.actions.debug_code import DebugCode
from metagpt.actions.execute_nb_code import ExecuteNbCode
from metagpt.actions.ml_action import UpdateDataColumns, WriteCodeWithToolsML
from metagpt.logs import logger
from metagpt.roles.code_interpreter import CodeInterpreter
from metagpt.tools.tool_data_type import ToolTypeEnum
from metagpt.utils.common import any_to_str


class MLEngineer(CodeInterpreter):
    debug_context: list = []
    latest_code: str = ""

    def __init__(self, name="Mark", profile="MLEngineer", **kwargs):
        super().__init__(name=name, profile=profile, **kwargs)

    async def _write_code(self):
        if not self.use_tools:
            return await super()._write_code()

        # In a trial and errors settings, check whether this is our first attempt to tackle the task. If there is no code execution before, then it is.
        is_first_trial = any_to_str(ExecuteNbCode) not in [msg.cause_by for msg in self.working_memory.get()]

        if is_first_trial:
            # For the first trial, write task code from scratch
            column_info = await self._update_data_columns()

            logger.info("Write code with tools")
            tool_context, code = await WriteCodeWithToolsML(selected_tools=self.tools).run(
                context=[],  # context assembled inside the Action
                plan=self.planner.plan,
                column_info=column_info,
            )
            self.debug_context = tool_context
            cause_by = WriteCodeWithToolsML

        else:
            # Previous trials resulted in error, debug and rewrite the code
            logger.warning("We got a bug, now start to debug...")
            code = await DebugCode().run(
                code=self.latest_code,
                runtime_result=self.working_memory.get(),
                context=self.debug_context,
            )
            logger.info(f"new code \n{code}")
            cause_by = DebugCode

        self.latest_code = code["code"]

        return code, cause_by

    async def _update_data_columns(self):
        current_task = self.planner.plan.current_task
        if current_task.task_type not in [
            ToolTypeEnum.DATA_PREPROCESS.value,
            ToolTypeEnum.FEATURE_ENGINEERING.value,
            ToolTypeEnum.MODEL_TRAIN.value,
        ]:
            return ""
        logger.info("Check columns in updated data")
        code = await UpdateDataColumns().run(self.planner.plan)
        success = False
        result, success = await self.execute_code.run(**code)
        print(result)
        return result if success else ""
