from metagpt.actions.ask_review import ReviewConst
from metagpt.actions.debug_code import DebugCode
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.ml_da_action import Reflect, SummarizeAnalysis, UpdateDataColumns
from metagpt.actions.write_analysis_code import WriteCodeWithToolsML
from metagpt.actions.write_code_steps import WriteCodeSteps
from metagpt.logs import logger
from metagpt.roles.code_interpreter import CodeInterpreter
from metagpt.roles.kaggle_manager import DownloadData, SubmitResult
from metagpt.schema import Message
from metagpt.utils.common import any_to_str


class MLEngineer(CodeInterpreter):
    use_code_steps: bool = False
    use_udfs: bool = False
    data_desc: dict = {}
    debug_context: list = []
    latest_code: str = ""

    def __init__(self, name="Mark", profile="MLEngineer", **kwargs):
        super().__init__(name=name, profile=profile, **kwargs)
        # self._watch([DownloadData, SubmitResult])  # in multi-agent settings

    async def _plan_and_act(self):
        ### a new attempt on the data, relevant in a multi-agent multi-turn setting ###
        await self._prepare_data_context()

        ### general plan process ###
        await super()._plan_and_act()

        ### summarize analysis ###
        summary = await SummarizeAnalysis().run(self.planner.plan)
        rsp = Message(content=summary, cause_by=SummarizeAnalysis)
        self.rc.memory.add(rsp)

        return rsp

    async def _write_and_exec_code(self, max_retry: int = 3):
        self.planner.current_task.code_steps = (
            await WriteCodeSteps().run(self.planner.plan) if self.use_code_steps else ""
        )

        code, result, success = await super()._write_and_exec_code(max_retry=max_retry)

        if success:
            if self.use_tools and self.planner.current_task.task_type in ["data_preprocess", "feature_engineering"]:
                update_success, new_code = await self._update_data_columns()
                if update_success:
                    code = code + "\n\n" + new_code

        return code, result, success

    async def _write_code(self):
        if not self.use_tools:
            return await super()._write_code()

        code_execution_count = sum([msg.cause_by == any_to_str(ExecutePyCode) for msg in self.working_memory.get()])

        if code_execution_count > 0:
            logger.warning("We got a bug code, now start to debug...")
            code = await DebugCode().run(
                code=self.latest_code,
                runtime_result=self.working_memory.get(),
                context=self.debug_context,
            )
            logger.info(f"new code \n{code}")
            cause_by = DebugCode

        else:
            logger.info("Write code with tools")
            tool_context, code = await WriteCodeWithToolsML().run(
                context=[],  # context assembled inside the Action
                plan=self.planner.plan,
                column_info=self.data_desc.get("column_info", ""),
            )
            self.debug_context = tool_context
            cause_by = WriteCodeWithToolsML

        self.latest_code = code

        return code, cause_by

    async def _update_data_columns(self):
        logger.info("Check columns in updated data")
        rsp = await UpdateDataColumns().run(self.planner.plan)
        is_update, code = rsp["is_update"], rsp["code"]
        success = False
        if is_update:
            result, success = await self.execute_code.run(code)
            if success:
                print(result)
                self.data_desc["column_info"] = result
        return success, code

    async def _prepare_data_context(self):
        memories = self.get_memories()
        if memories:
            latest_event = memories[-1].cause_by
            if latest_event == DownloadData:
                self.planner.plan.context = memories[-1].content
            elif latest_event == SubmitResult:
                # self reflect on previous plan outcomes and think about how to improve the plan, add to working  memory
                await self._reflect()

                # get feedback for improvement from human, add to working memory
                await self.planner.ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)

    async def _reflect(self):
        context = self.get_memories()
        context = "\n".join([str(msg) for msg in context])

        reflection = await Reflect().run(context=context)
        self.working_memory.add(Message(content=reflection, role="assistant"))
        self.working_memory.add(Message(content=Reflect.REWRITE_PLAN_INSTRUCTION, role="user"))
