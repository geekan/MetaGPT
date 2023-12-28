import json

from metagpt.actions.debug_code import DebugCode
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.ask_review import ReviewConst
from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools, MakeTools
from metagpt.actions.write_code_steps import WriteCodeSteps
from metagpt.const import PROJECT_ROOT
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import remove_comments
from metagpt.actions.ml_da_action import SummarizeAnalysis, Reflect, UpdateDataColumns
from metagpt.roles.code_interpreter import CodeInterpreter
from metagpt.roles.kaggle_manager import DownloadData, SubmitResult
from metagpt.tools.functions.libs.udf import UDFS_YAML


class MLEngineer(CodeInterpreter):
    def __init__(
        self, name="Mark", profile="MLEngineer", goal="", auto_run=False, use_tools=False, use_code_steps=False,
        make_udfs=False, use_udfs=False
    ):
        super().__init__(name=name, profile=profile, goal=goal, auto_run=auto_run)
        self._watch([DownloadData, SubmitResult])

        self.use_tools = use_tools
        self.use_code_steps = use_code_steps
        self.make_udfs = make_udfs   # user-defined functions
        self.use_udfs = use_udfs
        self.data_desc = {}
    
    async def _plan_and_act(self):
        
        ### Actions in a multi-agent multi-turn setting, a new attempt on the data ###
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
        
        ### general plan process ###
        await super()._plan_and_act()
        
        ### summarize analysis ###
        summary = await SummarizeAnalysis().run(self.planner.plan)
        rsp = Message(content=summary, cause_by=SummarizeAnalysis)
        self._rc.memory.add(rsp)
        
        return rsp

    async def _write_and_exec_code(self, max_retry: int = 3):
        self.planner.current_task.code_steps = (
            await WriteCodeSteps().run(self.planner.plan)
            if self.use_code_steps
            else ""
        )
        
        counter = 0
        success = False
        debug_context = []
        
        while not success and counter < max_retry:

            context = self.planner.get_useful_memories()

            if counter > 0 and (self.use_tools or self.use_udfs):
                logger.warning('We got a bug code, now start to debug...')
                code = await DebugCode().run(
                    plan=self.planner.current_task.instruction,
                    code=code,
                    runtime_result=self.working_memory.get(),
                    context=debug_context
                )
                logger.info(f"new code \n{code}")
                cause_by = DebugCode
            
            elif (not self.use_tools and not self.use_udfs) or (
                    self.planner.current_task.task_type == 'other' and not self.use_udfs):
                logger.info("Write code with pure generation")
                code = await WriteCodeByGenerate().run(
                    context=context, plan=self.planner.plan, temperature=0.0
                )
                debug_context = [self.planner.get_useful_memories(task_exclude_field={'result', 'code_steps'})[0]]
                cause_by = WriteCodeByGenerate
            
            else:
                logger.info("Write code with tools")
                if self.use_udfs:
                    # use user-defined function tools.
                    logger.warning("Writing code with user-defined function tools by WriteCodeWithTools.")
                    logger.info(f"Local user defined function as following:\
                        \n{json.dumps(list(UDFS_YAML.keys()), indent=2, ensure_ascii=False)}")
                    # set task_type to `udf`
                    self.planner.current_task.task_type = 'udf'
                    schema_path = UDFS_YAML
                else:
                    schema_path = PROJECT_ROOT / "metagpt/tools/functions/schemas"
                tool_context, code = await WriteCodeWithTools(schema_path=schema_path).run(
                    context=context,
                    plan=self.planner.plan,
                    column_info=self.data_desc.get("column_info", ""),
                )
                debug_context = tool_context
                cause_by = WriteCodeWithTools
            
            self.working_memory.add(
                Message(content=code, role="assistant", cause_by=cause_by)
            )
            
            result, success = await self.execute_code.run(code)
            print(result)
            # make tools for successful code and long code.
            if success and self.make_udfs and len(remove_comments(code).split('\n')) > 4:
                logger.info('Execute code successfully. Now start to make tools ...')
                await self.make_tools(code=code)
            self.working_memory.add(
                Message(content=result, role="user", cause_by=ExecutePyCode)
            )
            
            if "!pip" in code:
                success = False
            
            counter += 1
            
            if not success and counter >= max_retry:
                logger.info("coding failed!")
                review, _ = await self.planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORD[0] in review:
                    counter = 0  # redo the task again with help of human suggestions

        if success:
            if (self.use_tools and self.planner.current_task.task_type not in ['model_train', 'model_evaluate']) or self.use_udfs:
                update_success, new_code = await self._update_data_columns()
                if update_success:
                    code = code + "\n\n" + new_code

        return code, result, success
    
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
    
    async def _reflect(self):
        context = self.get_memories()
        context = "\n".join([str(msg) for msg in context])
        
        reflection = await Reflect().run(context=context)
        self.working_memory.add(Message(content=reflection, role="assistant"))
        self.working_memory.add(Message(content=Reflect.REWRITE_PLAN_INSTRUCTION, role="user"))

    async def make_tools(self, code: str):
        """Make user-defined functions(udfs, aka tools) for pure generation code.

        Args:
            code (str): pure generation code by class WriteCodeByGenerate.
        """
        logger.warning(f"Making tools for task_id {self.planner.current_task_id}: \
            `{self.planner.current_task.instruction}` \n code: \n {code}")
        make_tools = MakeTools()
        make_tool_retries, make_tool_current_retry = 3, 0
        while True:
            # start make tools
            tool_code = await make_tools.run(code, self.planner.current_task.instruction)
            make_tool_current_retry += 1

            # check tool_code by execute_code
            logger.info(f"Checking task_id {self.planner.current_task_id} tool code by executor...")
            execute_result, execute_success = await self.execute_code.run(tool_code)
            if not execute_success:
                logger.error(f"Tool code faild to execute, \n{execute_result}\n.We will try to fix it ...")
            # end make tools
            if execute_success or make_tool_current_retry >= make_tool_retries:
                if make_tool_current_retry >= make_tool_retries:
                    logger.error(f"We have tried the maximum number of attempts {make_tool_retries}\
                        and still have not created tools for task_id {self.planner.current_task_id} successfully,\
                            we will skip it.")
                break
        # save successful tool code in udf
        if execute_success:
            make_tools.save(tool_code)
