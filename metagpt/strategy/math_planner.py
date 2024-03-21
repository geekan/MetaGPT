
import json
from typing import List
from metagpt.logs import logger
from metagpt.actions.mi.ask_review import AskReview, ReviewConst

from metagpt.actions.mi.write_plan import (
    WritePlan,
    precheck_update_plan_from_rsp,
    update_plan_from_rsp,
)

from metagpt.schema import Message, Plan, Task
from metagpt.strategy.planner import Planner


MATH_STRUCTURAL_CONTEXT = """
## User Requirement
{user_requirement}
## Overall Plan
{tasks}

"""


class MathPlanner(Planner):

    async def update_plan(self, goal: str = "", max_tasks: int = 3, max_retries: int = 3):
        if goal:
            self.plan = Plan(goal=goal)

        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_last_useful_memories()
            rsp = await WritePlan().run(context, max_tasks=max_tasks, use_tools=self.use_tools)
            self.working_memory.add(Message(content=rsp, role="assistant", cause_by=WritePlan))

            # precheck plan before asking reviews
            is_plan_valid, error = precheck_update_plan_from_rsp(rsp, self.plan)
            if not is_plan_valid and max_retries > 0:
                error_msg = f"The generated plan is not valid with error: {error}, try regenerating, remember to generate either the whole plan or the single changed task only"
                logger.warning(error_msg)
                self.working_memory.add(Message(content=error_msg, role="assistant", cause_by=WritePlan))
                max_retries -= 1
                continue

            _, plan_confirmed = await self.ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)

        update_plan_from_rsp(rsp=rsp, current_plan=self.plan)

        self.working_memory.clear()

    def get_last_useful_memories(self, num=0) -> List[Message]:
        """find useful memories only to reduce context length and improve performance"""
        user_requirement = self.plan.goal
        tasks = [f"{task.task_id}:{task.instruction}" for task in self.plan.tasks]
        tasks = json.dumps(tasks, indent=4, ensure_ascii=False)

        context = MATH_STRUCTURAL_CONTEXT.format(
            user_requirement=user_requirement, tasks=tasks
        )
        context_msg = [Message(content=context, role="user")]

        return context_msg + self.working_memory.get(num)
