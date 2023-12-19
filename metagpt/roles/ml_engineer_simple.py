import re
from typing import List
import json
from datetime import datetime

import fire

from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.memory import Memory
from metagpt.logs import logger
from metagpt.actions.write_analysis_code import WriteCodeByGenerate
from metagpt.actions.ml_da_action import AskReview, ReviewConst
from metagpt.actions.execute_code import ExecutePyCode
from metagpt.roles.kaggle_manager import DownloadData
from metagpt.utils.save_code import save_code_file

STRUCTURAL_CONTEXT_SIMPLE = """
## User Requirement
{user_requirement}
## Data Description
{data_desc}
"""

JUDGE_PROMPT_TEMPLATE = """
# User Requirement
{user_requirement}
-----
# Context
{context}
-----
# State
Output "Ture" or "False". Judging from the code perspective, whether the user's needs have been completely fulfilled.
=====
# Finally output State, Thought and Next Action separately in one sentence
State:
Thought:
Next Action:
"""


class MLEngineerSimple(Role):
    def __init__(
            self, name="ABC", profile="MLEngineerSimple", goal="", auto_run: bool = False
    ):
        super().__init__(name=name, profile=profile, goal=goal)
        self._set_react_mode(react_mode="react")
        self._watch([DownloadData])
        self._init_actions([WriteCodeByGenerate, ExecutePyCode])

        self.goal = goal
        self.data_desc = ""
        self.use_tools = False
        self.use_code_steps = False
        self.execute_code = ExecutePyCode()
        self.auto_run = auto_run

        # memory for working on each task, discarded each time a task is done
        self.working_memory = Memory()

    async def _act(self):
        memories = self.get_memories()
        if memories:
            latest_event = memories[-1].cause_by
            if latest_event == DownloadData:
                self.data_desc = memories[-1].content

        await self._act_no_plan()

        # save code using datetime.now or  keywords related to the goal of your project (plan.goal).
        project_record = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_code_file(name=project_record, code_context=self.execute_code.nb, file_format="ipynb")

    async def _act_no_plan(self, max_retry: int = 20):
        counter = 0
        state = False
        while not state and counter < max_retry:
            context = self.get_useful_memories()
            print(f"memories数量：{len(context)}")
            # print("===\n" +str(context) + "\n===")
            code = await WriteCodeByGenerate().run(
                context=context, temperature=0.0
            )
            cause_by = WriteCodeByGenerate
            self.working_memory.add(
                Message(content=code, role="assistant", cause_by=cause_by)
            )

            result, success = await self.execute_code.run(code)
            print(result)
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

            completed_plan_memory = self.get_useful_memories()  # completed plan as a outcome
            self._rc.memory.add(completed_plan_memory[0])  # add to persistent memory
            prompt = JUDGE_PROMPT_TEMPLATE.format(user_requirement=self.goal, context=completed_plan_memory)
            rsp = await self._llm.aask(prompt)
            self.working_memory.add(
                Message(content=rsp, role="system")
            )

            matches = re.findall(r'\b(True|False)\b', rsp)
            state = False if 'False' in matches else True

    async def _ask_review(self, auto_run: bool = None, trigger: str = ReviewConst.TASK_REVIEW_TRIGGER):
        auto_run = auto_run or self.auto_run
        if not auto_run:
            context = self.get_useful_memories()
            review, confirmed = await AskReview().run(context=context[-5:], trigger=trigger)
            if not confirmed:
                self.working_memory.add(Message(content=review, role="user", cause_by=AskReview))
            return review, confirmed
        return "", True

    def get_useful_memories(self) -> List[Message]:
        """find useful memories only to reduce context length and improve performance"""
        user_requirement = self.goal
        context = STRUCTURAL_CONTEXT_SIMPLE.format(
            user_requirement=user_requirement, data_desc=self.data_desc
        )
        context_msg = [Message(content=context, role="user")]

        return context_msg + self.get_working_memories()

    def get_working_memories(self, num=6) -> List[Message]:
        return self.working_memory.get(num)   # 默认为6


if __name__ == "__main__":
    requirement = "Run data analysis on sklearn Iris dataset, include a plot"

    async def main(requirement: str = requirement, auto_run: bool = True):
        role = MLEngineerSimple(goal=requirement, auto_run=auto_run)
        await role.run(requirement)

    fire.Fire(main)
