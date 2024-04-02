# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import asyncio
from typing import Dict, List

from metagpt.actions.intent_detect import SentenceIntentDetect
from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import Message


class MGX(DataInterpreter):
    use_intent: bool = True
    intents: Dict = {}

    async def _intent_detect(self, user_msgs: List[Message] = None, **kwargs):
        todo = SentenceIntentDetect(context=self.context)
        await todo.run(user_msgs)
        logger.info(f"intent_desp is {todo.sop}")

        # Extract intent and sop prompt
        intention_ref = "\n".join([i.content for i in user_msgs])
        if todo.sop:
            self.intents[intention_ref] = todo.sop
            logger.debug(f"refs: {intention_ref}, sop: {todo.sop}")
            sop_str = "\n".join([f"- {i}" for i in todo.sop])
            markdown = (
                f"### User Requirement Detail\n```text\n{intention_ref}\n````\n"
                f"### Knowledge\nTo meet user requirements, the following standard operating procedure(SOP) must be"
                f" used. SOP descriptions cannot be modified; user requirements can only be appended to the end of corresponding steps.\n"
                f"{sop_str}"
            )
            return markdown
        return intention_ref

    async def _plan_and_act(self) -> Message:
        """first plan, then execute an action sequence, i.e. _think (of a plan) -> _act -> _act -> ... Use llm to come up with the plan dynamically."""

        # create initial plan and update it until confirmation
        goal = self.rc.memory.get()[-1].content  # retreive latest user requirement
        if self.use_intent:  # add mode
            user_message = Message(content=goal, role="user")
            goal = await self._intent_detect(user_msgs=[user_message])
        logger.info(f"Goal is {goal}")

        await self.planner.update_plan(goal=goal)

        # take on tasks until all finished
        while self.planner.current_task:
            task = self.planner.current_task
            logger.info(f"ready to take on task {task}")

            # take on current task
            task_result = await self._act_on_task(task)

            # process the result, such as reviewing, confirming, plan updating
            await self.planner.process_task_result(task_result)

        rsp = self.planner.get_useful_memories()[0]  # return the completed plan as a response

        self.rc.memory.add(rsp)  # add to persistent memory

        return rsp


if __name__ == "__main__":
    test_requirements = [
        "design a game using Gym (an open source Python library), including a graphical interface and interactive gameplay"
        # "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy"
        # "获取https://www.stats.gov.cn/sj/sjjd/202307/t20230718_1941322.html的内容，并返回上半年cpi的增长或下降幅度"
    ]

    for requirement in test_requirements:
        mgx = MGX()
        rsp = asyncio.run(mgx.run(requirement))
