from typing import List
import json
from datetime import datetime

import fire

from metagpt.actions import Action
from metagpt.actions.debug_code import DebugCode
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.ml_da_action import AskReview, SummarizeAnalysis, Reflect, ReviewConst
from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools, MakeTools
from metagpt.actions.write_code_steps import WriteCodeSteps
from metagpt.actions.write_plan import WritePlan
from metagpt.actions.write_plan import update_plan_from_rsp, precheck_update_plan_from_rsp
from metagpt.const import DATA_PATH, PROJECT_ROOT
from metagpt.logs import logger
from metagpt.memory import Memory
from metagpt.prompts.ml_engineer import STRUCTURAL_CONTEXT
from metagpt.prompts.ml_engineer import (
    UPDATE_DATA_COLUMNS,
    PRINT_DATA_COLUMNS
)
from metagpt.roles import Role
from metagpt.roles.kaggle_manager import DownloadData, SubmitResult
from metagpt.schema import Message, Plan
from metagpt.utils.common import remove_comments, create_func_config
from metagpt.utils.save_code import save_code_file
from metagpt.utils.recovery_util import save_history, load_history


class UpdateDataColumns(Action):
    async def run(self, plan: Plan = None) -> dict:
        finished_tasks = plan.get_finished_tasks()
        code_context = [remove_comments(task.code) for task in finished_tasks]
        code_context = "\n\n".join(code_context)
        prompt = UPDATE_DATA_COLUMNS.format(history_code=code_context)
        tool_config = create_func_config(PRINT_DATA_COLUMNS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        return rsp


class MLEngineer(Role):
    def __init__(
        self, name="ABC", profile="MLEngineer", goal="", auto_run: bool = False
    ):
        super().__init__(name=name, profile=profile, goal=goal)
        self._set_react_mode(react_mode="plan_and_act")
        self._watch([DownloadData, SubmitResult])
        
        self.plan = Plan(goal=goal)
        self.make_udfs = False   # user-defined functions
        self.use_udfs = False
        self.use_tools = True
        self.use_code_steps = True
        self.execute_code = ExecutePyCode()
        self.auto_run = auto_run
        self.data_desc = {}
        
        # memory for working on each task, discarded each time a task is done
        self.working_memory = Memory()
    
    async def _plan_and_act(self):
        
        ### Actions in a multi-agent multi-turn setting ###
        memories = self.get_memories()
        if memories:
            latest_event = memories[-1].cause_by
            if latest_event == DownloadData:
                self.plan.context = memories[-1].content
            elif latest_event == SubmitResult:
                # self reflect on previous plan outcomes and think about how to improve the plan, add to working  memory
                await self._reflect()
                
                # get feedback for improvement from human, add to working memory
                await self._ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)
        
        ### Common Procedure in both single- and multi-agent setting ###
        # create initial plan and update until confirmation
        await self._update_plan()
        
        while self.plan.current_task:
            task = self.plan.current_task
            logger.info(f"ready to take on task {task}")
            
            # take on current task
            code, result, success = await self._write_and_exec_code()
            
            # ask for acceptance, users can other refuse and change tasks in the plan
            review, task_result_confirmed = await self._ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)
            
            if self.auto_run:
                # if human confirms the task result, then we deem the task completed, regardless of whether the code run succeeds;
                # if auto mode, then the code run has to succeed for the task to be considered completed
                task_result_confirmed = success
            
            if task_result_confirmed:
                # tick off this task and record progress
                task.code = code
                task.result = result
                self.plan.finish_current_task()
                self.working_memory.clear()

                if self.use_tools or self.use_udfs:
                    success, new_code = await self._update_data_columns()
                    if success:
                        task.code = task.code + "\n\n" + new_code
                
                confirmed_and_more = (ReviewConst.CONTINUE_WORD[0] in review.lower()
                                      and review.lower() not in ReviewConst.CONTINUE_WORD[0])  # "confirm, ... (more content, such as changing downstream tasks)"
                if confirmed_and_more:
                    self.working_memory.add(Message(content=review, role="user", cause_by=AskReview))
                    await self._update_plan(review)
            
            elif "redo" in review:
                # Ask the Role to redo this task with help of review feedback,
                # useful when the code run is successful but the procedure or result is not what we want
                continue
            
            else:
                # update plan according to user's feedback and to take on changed tasks
                await self._update_plan(review)
        
        completed_plan_memory = self.get_useful_memories()  # completed plan as a outcome
        self._rc.memory.add(completed_plan_memory[0])  # add to persistent memory
        
        summary = await SummarizeAnalysis().run(self.plan)
        rsp = Message(content=summary, cause_by=SummarizeAnalysis)
        self._rc.memory.add(rsp)
        
        # save code using datetime.now or  keywords related to the goal of your project (plan.goal).
        project_record = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_code_file(name=project_record, code_context=self.execute_code.nb, file_format="ipynb")
        return rsp
    
    async def _update_data_columns(self):
        rsp = await UpdateDataColumns().run(self.plan)
        is_update, code = rsp["is_update"], rsp["code"]
        success = False
        if is_update:
            result, success = await self.execute_code.run(code)
            if success:
                self.data_desc["column_info"] = result
        return success, code
    
    async def _write_and_exec_code(self, max_retry: int = 3):
        self.plan.current_task.code_steps = (
            await WriteCodeSteps().run(self.plan)
            if self.use_code_steps
            else ""
        )
        
        counter = 0
        success = False
        debug_context = []
        
        while not success and counter < max_retry:
            context = self.get_useful_memories()
            if counter > 0 and (self.use_tools or self.use_udfs):
                logger.warning('We got a bug code, now start to debug...')
                code = await DebugCode().run(
                    plan=self.plan.current_task.instruction,
                    code=code,
                    runtime_result=self.working_memory.get(),
                    context=debug_context
                )
                logger.info(f"new code \n{code}")
                cause_by = DebugCode
            elif not self.use_tools or self.plan.current_task.task_type in ("other", "udf"):
                if self.use_udfs:
                    # use user-defined function tools.
                    from metagpt.tools.functions.libs.udf import UDFS_YAML
                    logger.warning("Writing code with user-defined function tools by WriteCodeWithTools.")
                    logger.info(f"Local user defined function as following:\
                        \n{json.dumps(list(UDFS_YAML.keys()), indent=2, ensure_ascii=False)}")
                    # set task_type to `udf`
                    self.plan.current_task.task_type = 'udf'
                    tool_context, code = await WriteCodeWithTools(schema_path=UDFS_YAML).run(
                        context=context,
                        plan=self.plan,
                        column_info=self.data_desc.get("column_info", ""),
                    )
                    debug_context = tool_context
                    cause_by = WriteCodeWithTools
                else:
                    logger.info("Write code with pure generation")
                    # TODO: 添加基于current_task.instruction-code_path的k-v缓存
                    code = await WriteCodeByGenerate().run(
                        context=context, plan=self.plan, temperature=0.0
                    )
                    debug_context = [self.get_useful_memories(task_exclude_field={'result', 'code_steps'})[0]]
                    cause_by = WriteCodeByGenerate
            else:
                logger.info("Write code with tools")
                schema_path = PROJECT_ROOT / "metagpt/tools/functions/schemas"
                tool_context, code = await WriteCodeWithTools(schema_path=schema_path).run(
                    context=context,
                    plan=self.plan,
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
            if success and self.make_udfs and len(code.split('\n')) > 4:
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
                review, _ = await self._ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                if ReviewConst.CHANGE_WORD[0] in review:
                    counter = 0  # redo the task again with help of human suggestions
        
        return code, result, success
    
    async def _ask_review(self, auto_run: bool = None, trigger: str = ReviewConst.TASK_REVIEW_TRIGGER):
        auto_run = auto_run or self.auto_run
        if not auto_run:
            context = self.get_useful_memories()
            review, confirmed = await AskReview().run(context=context[-5:], plan=self.plan, trigger=trigger)
            if not confirmed:
                self.working_memory.add(Message(content=review, role="user", cause_by=AskReview))
            return review, confirmed
        return "", True
    
    async def _update_plan(self, review: str = "", max_tasks: int = 3, max_retries: int = 3):
        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await WritePlan().run(
                context, max_tasks=max_tasks, use_tools=self.use_tools
            )
            self.working_memory.add(
                Message(content=rsp, role="assistant", cause_by=WritePlan)
            )
            
            # precheck plan before asking reviews
            is_plan_valid, error = precheck_update_plan_from_rsp(rsp, self.plan)
            if not is_plan_valid and max_retries > 0:
                error_msg = f"The generated plan is not valid with error: {error}, try regenerating, remember to generate either the whole plan or the single changed task only"
                logger.warning(error_msg)
                self.working_memory.add(Message(content=error_msg, role="assistant", cause_by=WritePlan))
                max_retries -= 1
                continue
            
            _, plan_confirmed = await self._ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)
        
        update_plan_from_rsp(rsp, self.plan)
        
        self.working_memory.clear()
    
    async def _reflect(self):
        context = self.get_memories()
        context = "\n".join([str(msg) for msg in context])
        
        reflection = await Reflect().run(context=context)
        self.working_memory.add(Message(content=reflection, role="assistant"))
        self.working_memory.add(Message(content=Reflect.REWRITE_PLAN_INSTRUCTION, role="user"))
    
    def get_useful_memories(self, task_exclude_field=None) -> List[Message]:
        """find useful memories only to reduce context length and improve performance"""
        # TODO dataset description , code steps
        if task_exclude_field is None:
            # Shorten the context as we don't need code steps after we get the codes.
            # This doesn't affect current_task below, which should hold the code steps
            task_exclude_field = {'code_steps'}
        user_requirement = self.plan.goal
        data_desc = self.plan.context
        tasks = [task.dict(exclude=task_exclude_field) for task in self.plan.tasks]
        tasks = json.dumps(tasks, indent=4, ensure_ascii=False)
        current_task = self.plan.current_task.json() if self.plan.current_task else {}
        context = STRUCTURAL_CONTEXT.format(
            user_requirement=user_requirement, data_desc=data_desc, tasks=tasks, current_task=current_task
        )
        context_msg = [Message(content=context, role="user")]
        
        return context_msg + self.get_working_memories()
    
    def get_working_memories(self) -> List[Message]:
        return self.working_memory.get()

    def reset(self):
        """Restart role with the same goal."""
        self.plan = Plan(goal=self.plan.goal)
        self.execute_code = ExecutePyCode()

    async def make_tools(self, code: str):
        """Make user-defined functions(udfs, aka tools) for pure generation code.

        Args:
            code (str): pure generation code by class WriteCodeByGenerate.
        """
        logger.warning(f"Making tools for task_id {self.plan.current_task_id}: \
            `{self.plan.current_task.instruction}` \n code: \n {code}")
        make_tools = MakeTools()
        code_prompt = f"The following code is about {self.plan.current_task.instruction},\
            convert it to be a General Function, {code}"
        tool_code = await make_tools.run(code_prompt)
        # check tool_code by execute_code
        logger.info(f"Checking task_id {self.plan.current_task_id} tool code by executor...")
        _, success = await self.execute_code.run(tool_code)
        make_tool_retries, make_tool_current_retry = 3, 1
        while not success:
            tool_code = await make_tools.run(code_prompt)
            _, success = await self.execute_code.run(tool_code)
            if make_tool_current_retry > make_tool_retries:
                logger.error(f"We have tried the maximum number of attempts {make_tool_retries}\
                    and still have not created tools for task_id {self.plan.current_task_id} successfully,\
                        we will skip it.")
                break
        # save successful tool code in udf
        if success:
            make_tools.save(tool_code)


if __name__ == "__main__":
    # requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    # requirement = "Run data analysis on sklearn Diabetes dataset, include a plot"
    # requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy"
    # requirement = "Run data analysis on sklearn Wisconsin Breast Cancer dataset, include a plot, train a model to predict targets (20% as validation), and show validation accuracy"
    # requirement = "Run EDA and visualization on this dataset, train a model to predict survival, report metrics on validation set (20%), dataset: workspace/titanic/train.csv"

    # async def main(requirement: str = requirement, auto_run: bool = True):
    #     role = MLEngineer(goal=requirement, auto_run=auto_run)
    #     # make udfs
    #     role.make_udfs = True
    #     role.use_udfs = False
    #     await role.run(requirement)
    #     # use udfs
    #     role.reset()
    #     role.make_udfs = False
    #     role.use_udfs = True
    #     await role.run(requirement)

    
    # requirement = "Perform data analysis on the provided data. Train a model to predict the target variable Survived. Include data preprocessing, feature engineering, and modeling in your pipeline. The metric is accuracy."
    
    # data_path = f"{DATA_PATH}/titanic"
    # requirement = f"This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv'."
    # requirement = f"Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy"
    # data_path = f"{DATA_PATH}/icr-identify-age-related-conditions"
    # requirement = f"This is a medical dataset with over fifty anonymized health characteristics linked to three age-related conditions. Your goal is to predict whether a subject has or has not been diagnosed with one of these conditions.The target column is Class. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report f1 score on the eval data. Train data path: {data_path}/split_train.csv, eval data path: {data_path}/split_eval.csv."
    
    # data_path = f"{DATA_PATH}/santander-customer-transaction-prediction"
    # requirement = f"This is a customers financial dataset. Your goal is to predict which customers will make a specific transaction in the future. The target column is target. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report F1 Score on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv' ."
    
    data_path = f"{DATA_PATH}/house-prices-advanced-regression-techniques"
    requirement = f"This is a house price dataset, your goal is to predict the sale price of a property based on its features. The target column is SalePrice. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report RMSE between the logarithm of the predicted value and the logarithm of the observed sales price on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv'."
    
    save_dir = ""
    
    
    # save_dir = DATA_PATH / "output" / "2023-12-14_20-40-34"
    
    async def main(requirement: str = requirement, auto_run: bool = True, save_dir: str = save_dir):
        """
        The main function to run the MLEngineer with optional history loading.

        Args:
            requirement (str): The requirement for the MLEngineer.
            auto_run (bool): Whether to auto-run the MLEngineer.
            save_dir (str): The directory from which to load the history or to save the new history.

        Raises:
            Exception: If an error occurs during execution, log the error and save the history.
        """
        if save_dir:
            logger.info("Resuming from history trajectory")
            plan, nb = load_history(save_dir)
            role = MLEngineer(goal=requirement, auto_run=auto_run)
            role.plan = Plan(**plan)
            role.execute_code = ExecutePyCode(nb)
        
        else:
            logger.info("Run from scratch")
            role = MLEngineer(goal=requirement, auto_run=auto_run)
        
        try:
            await role.run(requirement)
        except Exception as e:
            
            save_path = save_history(role, save_dir)
            
            logger.exception(f"An error occurred: {e}, save trajectory here: {save_path}")
    
    
    fire.Fire(main)
