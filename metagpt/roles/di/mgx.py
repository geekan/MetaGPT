# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import asyncio
import json
from typing import Dict, List

from metagpt.actions.intent_detect import IntentDetect
from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import Message


class MGX(DataInterpreter):
    use_intent: bool = True
    intents: Dict = {}

    async def _intent_detect(self, user_msgs: List[Message] = None, **kwargs):
        todo = IntentDetect(context=self.context)
        intent_desp = await todo.run(user_msgs)
        intent_desp = json.loads(intent_desp.content)
        logger.info(f"intent_desp is {intent_desp}")

        # Extract intent and sop prompt
        intents = intent_desp.get("intentions", [{}])[0]
        # Optional: handle the case where intentions might be empty or malformatted
        intention_ref = intents.get("intention", {}).get("refs", [None])[0]
        sop = intents.get("sop", {}).get("sop", None)
        self.intents.update({intention_ref: sop})

        if sop is None:
            return intention_ref
        return intention_ref + "\n---" + "\n".join(intents["sop"]["sop"])

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
