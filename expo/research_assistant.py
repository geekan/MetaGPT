from __future__ import annotations

import json
import os

from pydantic import model_validator

from expo.utils import mcts_logger, save_notebook
from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.const import SERDESER_PATH
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import Message, Task, TaskResult
from metagpt.utils.common import CodeParser, write_json_file

EXTRACT_SCORE_PROMPT = """
# Code:
{code}

# Execution Result:
{result}

# Instruction:
Based on the code and execution result, please extract the scores and return it as a dictionary.
If you cannot find the scores, please still return a dictionary with the keys 'train_score', 'dev_score', and 'test_score', and set the values to -1.

# Format:
```json
{{
    "train_score": x.x,
    "dev_score": x.x,
    "test_score": x.x
}}
```
"""


class ResearchAssistant(DataInterpreter):
    node_id: str = "0"
    start_task_id: int = 1
    state_saved: bool = False
    role_dir: str = SERDESER_PATH.joinpath("team", "environment", "roles", "Experimenter")

    def get_node_name(self):
        return f"Node-{self.node_id}"

    def get_next_instruction(self):
        return self.planner.plan.tasks[self.start_task_id]

    def change_next_instruction(self, new_instruction):
        if new_instruction is not None:
            self.planner.plan.task_map[str(self.start_task_id)].instruction = new_instruction
            self.remap_tasks()

    def update_til_start_task(self, role: ResearchAssistant, backward: bool = True):
        if backward:
            # make sure the previous task instructions are matched
            assert (
                self.start_task_id == role.start_task_id - 1
            ), f"start_task_id: {self.start_task_id}, role.start_task_id: {role.start_task_id}"
            for i in range(self.start_task_id):
                if (
                    self.planner.plan.task_map[str(self.start_task_id)].instruction
                    != role.planner.plan.task_map[str(self.start_task_id)].instruction
                ):
                    mcts_logger.info("Previous task instructions not matched")
                    self.remap_tasks()
                    return
            # copy new role's task (self.start_task_id) to current role
            self.planner.plan.task_map[str(self.start_task_id)] = role.planner.plan.task_map[
                str(self.start_task_id)
            ].model_copy()
            self.remap_tasks()

        else:
            assert (
                self.start_task_id == role.start_task_id + 1
            ), f"start_task_id: {self.start_task_id}, role.start_task_id: {role.start_task_id}"
            if int(role.planner.plan.current_task_id) > self.start_task_id:
                for i in range(role.start_task_id):
                    self.planner.plan.task_map[str(i)] = role.planner.plan.task_map[str(i)].model_copy()
            self.remap_tasks()

    async def get_score(self):
        score_dict = await self.llm_extract_score()
        score_dict["score"] = score_dict["dev_score"]
        return score_dict

    async def llm_extract_score(self):
        result_text = self.planner.plan.task_map[str(len(self.planner.plan.task_map))].result
        code_text = self.planner.plan.task_map[str(len(self.planner.plan.task_map))].code
        rsp = await self.llm.aask(EXTRACT_SCORE_PROMPT.format(code=code_text, result=result_text, role="user"))
        json_block = CodeParser.parse_code(block=None, text=rsp)
        score_dict = json.loads(json_block)
        return score_dict

    @model_validator(mode="after")
    def set_plan_and_tool(self) -> "Interpreter":
        if self.planner.plan.goal != "":
            self.set_actions([WriteAnalysisCode])
            self._set_state(0)
            print("Plan already exists, skipping initialization.")
            return self
        print("Initializing plan and tool...")
        return super().set_plan_and_tool()

    async def _act_on_task(self, current_task: Task) -> TaskResult:
        """Useful in 'plan_and_act' mode. Wrap the output in a TaskResult for review and confirmation."""
        mcts_logger.info(f"The current_task is: {current_task}")
        code, result, is_success = await self._write_and_exec_code()
        task_result = TaskResult(code=code, result=result, is_success=is_success)
        if int(current_task.task_id) == self.start_task_id + 1:
            # fe_id = current_task.dependent_task_ids
            self.save_state()
            save_notebook(role=self, save_dir=self.role_dir, name=self.get_node_name())
        return task_result

    def save_state(self, static_save=False):
        if self.state_saved and not static_save:
            return
        if not static_save:
            self.state_saved = True
            mcts_logger.log("MCTS", f"Saving state at task {self.start_task_id}")
        else:
            mcts_logger.log("MCTS", "Static Saving")
        stg_path = self.role_dir
        name = self.get_node_name()
        role_path = os.path.join(stg_path, f"{name}.json")
        # 将状态保存为 JSON 文件
        write_json_file(role_path, self.model_dump())

    def remap_tasks(self):
        self.planner.plan.tasks = [
            self.planner.plan.task_map[task_id] for task_id in sorted(self.planner.plan.task_map.keys())
        ]

    async def run(self, with_message=None) -> Message | None:
        """Observe, and think and act based on the results of the observation"""
        if with_message == "continue":
            # self.set_todo(None)
            # working_memory = self.working_memory
            # self.remap_tasks()
            mcts_logger.info("Continue to run")
            self.rc.working_memory.clear()
            self.working_memory.clear()
            # self.rc.todo = WriteAnalysisCode()
            rsp = await self.react()
            # 发送响应消息给 Environment 对象，以便它将消息传递给订阅者
            self.set_todo(None)
            self.publish_message(rsp)
            return rsp
        return await super().run(with_message)
