from __future__ import annotations

import asyncio
import json
import os

from pydantic import model_validator

from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.const import SERDESER_PATH
from metagpt.ext.sela.utils import mcts_logger, save_notebook
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import Message, Task, TaskResult
from metagpt.utils.common import CodeParser, write_json_file

CODE_BLOCK_RESULT = """
## Code:
{code}

## Execution Result:
{result}
"""

EXTRACT_SCORE_PROMPT = """
# Code Blocks
{code_block}
# Instruction:
Based on the code and execution result, please extract the **final scores** and return it as a dictionary.
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


class TimeoutException(Exception):
    pass


def async_timeout():
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            try:
                result = await asyncio.wait_for(func(self, *args, **kwargs), timeout=self.role_timeout)
            except asyncio.TimeoutError:
                text = f"Function timed out after {self.role_timeout} seconds"
                mcts_logger.error(text)
                self.save_state()
                raise TimeoutException(text)
            return result

        return wrapper

    return decorator


class Experimenter(DataInterpreter):
    node_id: str = "0"
    start_task_id: int = 1
    state_saved: bool = False
    role_dir: str = SERDESER_PATH.joinpath("team", "environment", "roles", "Experimenter")
    role_timeout: int = 1000

    def get_node_name(self):
        return f"Node-{self.node_id}"

    def get_next_instruction(self):
        return self.planner.plan.tasks[self.start_task_id].instruction

    def change_next_instruction(self, new_instruction):
        if new_instruction is not None:
            self.planner.plan.task_map[str(self.start_task_id)].instruction = new_instruction
            self.remap_tasks()

    def update_til_start_task(self, role: Experimenter, backward: bool = True):
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
        # result_text = self.planner.plan.task_map[str(len(self.planner.plan.task_map))].result
        # code_text = self.planner.plan.task_map[str(len(self.planner.plan.task_map))].code
        num_tasks = len(self.planner.plan.task_map)
        task_map = self.planner.plan.task_map
        code_block = "\n".join(
            [
                CODE_BLOCK_RESULT.format(code=task_map[str(i + 1)].code, result=task_map[str(i + 1)].result)
                for i in range(num_tasks)
            ]
        )
        rsp = await self.llm.aask(EXTRACT_SCORE_PROMPT.format(code_block=code_block, role="user"))
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
            save_notebook(role=self, save_dir=self.role_dir, name=self.get_node_name(), save_to_depth=True)
        else:
            save_notebook(role=self, save_dir=self.role_dir, name=self.get_node_name())
        return task_result

    def get_solution(self):
        codes = [task.code for task in self.planner.plan.tasks]
        results = [task.result for task in self.planner.plan.tasks]
        return {"codes": codes, "results": results}

    def save_state(self, static_save=False):
        """
        attribute:
            state_saved - the state has been saved
        input:
            static_save - saving the state without changing the state_saved flag - used when a new role is created
        """
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
        # save state as json file
        write_json_file(role_path, self.model_dump())

    def remap_tasks(self):
        self.planner.plan.tasks = [
            self.planner.plan.task_map[task_id] for task_id in sorted(self.planner.plan.task_map.keys())
        ]

    @async_timeout()
    async def run(self, with_message=None) -> Message | None:
        """Observe, and think and act based on the results of the observation"""
        if with_message == "continue":
            mcts_logger.info("Continue to run")
            self.rc.working_memory.clear()
            self.working_memory.clear()
            rsp = await self.react()
            self.set_todo(None)
            self.publish_message(rsp)
            return rsp
        return await super().run(with_message)
