import json
import re
from typing import List

import fire
import pandas as pd

from metagpt.actions import Action
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.actions.write_analysis_code import WriteCodeByGenerate, WriteCodeWithTools
from metagpt.actions.write_code_steps import WriteCodeSteps
from metagpt.actions.write_plan import WritePlan
from metagpt.const import DATA_PATH
from metagpt.logs import logger
from metagpt.prompts.ml_engineer import GEN_DATA_DESC_PROMPT
from metagpt.roles import Role
from metagpt.schema import Message, Plan
from metagpt.utils.common import CodeParser
from metagpt.actions.debug_code import DebugCode

STRUCTURAL_CONTEXT = """
## User Requirement
{user_requirement}
## Dataset Description
{data_desc}
## Current Plan
{tasks}
## Current Task
{current_task}
## Packages Installed
scikit-learn
pandas
numpy
lightgbm
xgboost
catboost
"""


def truncate(result: str, keep_len: int = 1000) -> str:
    desc = "Truncated to show only the last 1000 characters\n"
    if result.startswith(desc):
        result = result[-len(desc):]
    
    if len(result) > keep_len:
        result = result[-keep_len:]
    
    if not result.startswith(desc):
        return desc + result
    return desc


def remove_escape_and_color_codes(input_str):
    # 使用正则表达式去除转义字符和颜色代码
    pattern = re.compile(r'\x1b\[[0-9;]*[mK]')
    result = pattern.sub('', input_str)
    return result


def read_data(file: str) -> pd.DataFrame:
    if file.endswith(".csv"):
        df = pd.read_csv(file, sep=",")
        sep_list = [";", "\t", ":", " ", "|"]
        for sep in sep_list:
            if df.shape[1] == 1:
                df = pd.read_csv(file, sep=sep)
            else:
                break
    else:
        raise ValueError(f"Unsupported file type: {file}")
    return df


def get_column_info(df: pd.DataFrame) -> str:
    data = []
    for i in df.columns:
        nan_freq = float("%.2g" % (df[i].isna().mean() * 100))
        n_unique = df[i].nunique()
        data.append([i, df[i].dtype, nan_freq, n_unique])
    
    samples = pd.DataFrame(
        data,
        columns=["Column_name", "Data_type", "NaN_Frequency(%)", "N_unique"],
    )
    return samples.to_string(index=False)


class AskReview(Action):
    async def run(self, context: List[Message], plan: Plan = None):
        logger.info("Current overall plan:")
        logger.info(
            "\n".join([f"{task.task_id}: {task.instruction}, is_finished: {task.is_finished}" for task in plan.tasks])
        )
        
        logger.info("most recent context:")
        latest_action = context[-1].cause_by.__name__ if context[-1].cause_by else ""
        prompt = f"\nPlease review output from {latest_action}:\n" \
                 "If you want to change a task in the plan, say 'change task task_id, ... (things to change)'\n" \
                 "If you confirm the output and wish to continue with the current process, type CONFIRM\n" \
                 "If you want to terminate the process, type exit:\n"
        rsp = input(prompt)
        
        if rsp.lower() in ("exit"):
            exit()
        
        confirmed = rsp.lower() in ("confirm", "yes", "y")
        
        return rsp, confirmed


class GenerateDataDesc(Action):
    async def run(self, file: str) -> dict:
        data_desc = {}
        df = read_data(file)
        data_head = df.head().to_dict(orient="list")
        data_head = json.dumps(data_head, indent=4, ensure_ascii=False)
        prompt = GEN_DATA_DESC_PROMPT.replace("{data_head}", data_head)
        rsp = await self._aask(prompt)
        rsp = CodeParser.parse_code(block=None, text=rsp)
        rsp = json.loads(rsp)
        data_desc["path"] = file
        data_desc["data_desc"] = rsp["data_desc"]
        data_desc["column_desc"] = rsp["column_desc"]
        data_desc["column_info"] = get_column_info(df)
        return data_desc


class MLEngineer(Role):
    def __init__(
            self, name="ABC", profile="MLEngineer", goal="", auto_run: bool = False, data_path: str = None
    ):
        super().__init__(name=name, profile=profile, goal=goal)
        self._set_react_mode(react_mode="plan_and_act")
        self.plan = Plan(goal=goal)
        self.use_tools = True
        self.use_code_steps = True
        self.execute_code = ExecutePyCode()
        self.auto_run = auto_run
        self.data_path = data_path
        self.data_desc = {}
    
    async def _plan_and_act(self):
        if self.data_path:
            self.data_desc = await self._generate_data_desc()
        
        # create initial plan and update until confirmation
        await self._update_plan()
        
        while self.plan.current_task:
            task = self.plan.current_task
            logger.info(f"ready to take on task {task}")
            
            # take on current task
            code, result, success, code_steps = await self._write_and_exec_code()
            
            # ask for acceptance, users can other refuse and change tasks in the plan
            task_result_confirmed = await self._ask_review()
            
            # 针对当前task进行单独plan
            if not success or not task_result_confirmed:
                # fixme: 增加对应plan
                self.state.plan()
                
            if success and task_result_confirmed:
                # tick off this task and record progress
                task.code = code
                task.result = result
                task.code_steps = code_steps
                self.plan.finish_current_task()
                self.working_memory.clear()
                
                if "print(df_processed.info())" in code:
                    self.data_desc["column_info"] = result
            else:
                # update plan according to user's feedback and to take on changed tasks
                await self._update_plan()
        
        finished_tasks = self.plan.get_finished_tasks()
        if len(finished_tasks) == len(self.plan.tasks):
            code_context = [task.code for task in finished_tasks]
            code_context = "\n\n".join(code_context)
            result, success = await self.execute_code.run(code_context)
            # truncated the result
            print(truncate(result))
    
    async def _generate_data_desc(self):
        data_desc = await GenerateDataDesc().run(self.data_path)
        return data_desc
    
    async def _write_and_exec_code(self, max_retry: int = 3):
        code_steps = (
            await WriteCodeSteps().run(self.plan)
            if self.use_code_steps
            else ""
        )
        
        counter = 0
        improve_code = ""
        success = False
        
        finished_tasks = self.plan.get_finished_tasks()
        code_context = [task.code for task in finished_tasks]
        code_result = [task.result for task in finished_tasks]
        code_context = "\n\n".join(code_context)
        code_result = "\n\n".join(code_result)
        
        while not success and counter < max_retry:
            if counter == 0:
                context = self.get_useful_memories()
            else:
                improve_code = await DebugCode().run(plan=self.plan.current_task.instruction,
                                                     finished_code=code_context,
                                                     finished_code_result=code_result,
                                                     code=code,
                                                     runtime_result=self.working_memory.get())
            
            if not self.use_tools or self.plan.current_task.task_type == "other":
                logger.info("Write code with pure generation")
                
                code = await WriteCodeByGenerate().run(
                    context=context, plan=self.plan, code_steps=code_steps, temperature=0.0
                )
                cause_by = WriteCodeByGenerate
            else:
                logger.info("Write code with tools")
                
                if improve_code != "":
                    code = improve_code
                    logger.info(f"new code {code}")
                    cause_by = DebugCode
                else:
                    code = await WriteCodeWithTools().run(
                        context=context, plan=self.plan, code_steps=code_steps, **{"column_names": {}}
                    )
                    
                    cause_by = WriteCodeWithTools
            
            self.working_memory.add(
                Message(content=code, role="assistant", cause_by=cause_by)
            )
            
            # debug on code, run on runcode with finished code and new_df
            # runcode = code_context + "\n\n" + code
            runcode = code
            
            result, success = await self.execute_code.run(runcode)
            # truncated the result
            print(truncate(result))
            
            self.working_memory.add(
                Message(content=truncate(remove_escape_and_color_codes(result)), role="user", cause_by=ExecutePyCode)
            )
            
            if "!pip" in code:
                 success = False
            # if not success:
            #     await self._ask_review()
            
            counter += 1
        
        success = False
        
        return code, result, success, code_steps
    
    async def _ask_review(self):
        if not self.auto_run:
            context = self.get_useful_memories()
            review, confirmed = await AskReview().run(context=context[-5:], plan=self.plan)
            if not confirmed:
                self.working_memory.add(Message(content=review, role="user", cause_by=AskReview))
            return confirmed
        return True
    
    async def _update_plan(self, max_tasks: int = 3):
        plan_confirmed = False
        
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await WritePlan().run(
                context, max_tasks=max_tasks, use_tools=self.use_tools
            )
            self.working_memory.add(
                Message(content=rsp, role="assistant", cause_by=WritePlan)
            )
            plan_confirmed = await self._ask_review()
        
        new_tasks = WritePlan.rsp_to_tasks(rsp)
        logger.debug(len(self.plan.tasks))
        logger.debug(len(new_tasks))
        ## fixme: 能重复执行多轮重新plan，但应该有更优处理逻辑
        ## fixme: do not overwrite original tasks
        tasks = self.plan.tasks + new_tasks
        
        self.plan.add_tasks(tasks)
        self.working_memory.clear()
    
    def get_useful_memories(self) -> List[Message]:
        """find useful memories only to reduce context length and improve performance"""
        # TODO dataset description , code steps
        user_requirement = self.plan.goal
        tasks = json.dumps(
            [task.dict() for task in self.plan.tasks], indent=4, ensure_ascii=False
        )
        current_task = self.plan.current_task.json() if self.plan.current_task else {}
        context = STRUCTURAL_CONTEXT.format(
            user_requirement=user_requirement,
            data_desc=self.data_desc,
            tasks=tasks,
            current_task=current_task
        )
        context_msg = [Message(content=context, role="user")]
        
        return context_msg + self.working_memory.get()
    
    @property
    def working_memory(self):
        return self._rc.memory


if __name__ == "__main__":
    # requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    # requirement = "Run data analysis on sklearn Diabetes dataset, include a plot"
    # requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy"
    # requirement = "Run data analysis on sklearn Wisconsin Breast Cancer dataset, include a plot, train a model to predict targets (20% as validation), and show validation accuracy"
    # requirement = "Run EDA and visualization on this dataset, train a model to predict survival, report metrics on validation set (20%), dataset: workspace/titanic/train.csv"
    
    # requirement = "Perform data analysis on the provided data. Train a model to predict the target variable Survived. Include data preprocessing, feature engineering, and modeling in your pipeline. The metric is accuracy."
    
    data_path = f"{DATA_PATH}/titanic"
    requirement = f"This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '{data_path}/split_train.csv', eval data path: '{data_path}/split_eval.csv'."
    
    
    async def main(requirement: str = requirement, auto_run: bool = True, data_path: str = ""):
        role = MLEngineer(goal=requirement, auto_run=auto_run, data_path=data_path)
        await role.run(requirement)
    
    
    fire.Fire(main)
