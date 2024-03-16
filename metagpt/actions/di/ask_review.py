from __future__ import annotations

from typing import Literal, Tuple

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message, Plan
from metagpt.utils.common import CodeParser


class ReviewConst:
    TASK_REVIEW_TRIGGER = "task"
    CODE_REVIEW_TRIGGER = "code"
    PLAN_REVIEW_TRIGGER = "plan"
    CONTINUE_WORDS = ["confirm", "continue", "c", "yes", "y"]
    CHANGE_WORDS = ["change"]
    EXIT_WORDS = ["exit"]
    GOAL_FINISHED_WORDS = ["finished", "done"]
    REDO_WORDS = ["redo"]
    TASK_REVIEW_INSTRUCTION = (
        f"If you want to change, add, delete a task or merge tasks in the plan, type '{CHANGE_WORDS[0]} task task_id or current task, ... (things to change)' "
        f"If you confirm the output from the current task and wish to continue, type: {CONTINUE_WORDS[0]}"
        f"If the code does not match the *instruction* in `## Current Task`, type: {REDO_WORDS[0]}, ..., (reason for doing it again)"
        f"If the `## User Requirement` has already been accomplished, type: {GOAL_FINISHED_WORDS[0]}."
    )
    CODE_REVIEW_INSTRUCTION = (
        f"If you want the codes to be rewritten, type '{CHANGE_WORDS[0]} ... (your change advice)' "
        f"If you want to leave it as is, type: {CONTINUE_WORDS[0]} or {CONTINUE_WORDS[1]}"
    )
    EXIT_INSTRUCTION = f"If you want to terminate the process, type: {EXIT_WORDS[0]}"
    SYS_MSG = (
        "You are very good at reviewing any code, task, and plan, {instruction}"
        "your reflecting and reviewing result must start with '```\n' and end with '\n```', like ```\nconfirm\n```"
        "**Notice: The starting word in your suggestions must be one of the following:"
        f"{CHANGE_WORDS[0]}, {CONTINUE_WORDS[0]}, {GOAL_FINISHED_WORDS[0]}, {REDO_WORDS[0]} **"
    ).replace("type", "return")
    ASK_HUMAN_FOR_HELP = (
        "The task code execution failed, we need your help, please provide new solution ideas,"
        f"or type {EXIT_WORDS[0]} to terminate the code"
    )
    PLAN_REVIEW_INSTRUCTION = (
        "You first determine the requirement type and analyze the necessary information and tasks to complete it."
        "Analyze what are the common unknown information that need to be explored, and whether there are tasks to explore it."
        "Then, review the reasonableness of the tasks orders and relations in the plan."
        f"If you confirm the plan, respond: ```\nconfirm\n```,"
        f"If you want make new plan, respond: ```\n{CHANGE_WORDS[0]}, (your review result)\n```,"
    )
    INSTRUCTIONS = {
        TASK_REVIEW_TRIGGER: TASK_REVIEW_INSTRUCTION,
        CODE_REVIEW_TRIGGER: CODE_REVIEW_INSTRUCTION,
        PLAN_REVIEW_TRIGGER: PLAN_REVIEW_INSTRUCTION,
    }


class AskReview(Action):
    async def run(
        self,
        context: list[Message] = [],
        plan: Plan = None,
        trigger: str = ReviewConst.TASK_REVIEW_TRIGGER,
        review_type: Literal["human", "llm", "disabled"] = "disabled",
    ) -> Tuple[str, bool]:
        if plan:
            logger.info("Current overall plan:")
            logger.info(
                "\n".join(
                    [f"{task.task_id}: {task.instruction}, is_finished: {task.is_finished}" for task in plan.tasks]
                )
            )

        logger.info("Most recent context:")
        latest_action = context[-1].cause_by if context and context[-1].cause_by else ""
        review_instruction = ReviewConst.INSTRUCTIONS[trigger]

        prompt = (
            f"This is a <{trigger}> review. Please review output from {latest_action}\n"
            f"{review_instruction}\n"
            f"{ReviewConst.EXIT_INSTRUCTION}\n"
            "Please type your review below:\n"
        )

        if review_type == "human":
            rsp = input(prompt)
        elif review_type == "llm":
            llm_rsp = await self.llm.aask(
                msg="\n".join([str(c) for c in context]),
                system_msgs=[ReviewConst.SYS_MSG.format(instruction=review_instruction)],
            )
            rsp = CodeParser.parse_code(None, llm_rsp).strip()
        else:
            rsp = "confirm"

        if rsp.lower() in ReviewConst.EXIT_WORDS:
            exit()

        if rsp.lower() in ReviewConst.GOAL_FINISHED_WORDS:
            plan.finished_all_tasks()
            exit()

        # Confirmation can be one of "confirm", "continue", "c", "yes", "y" exactly, or sentences containing "confirm".
        # One could say "confirm this task, but change the next task to ..."
        if review_type == "human":
            confirmed = rsp.lower() in ReviewConst.CONTINUE_WORDS or ReviewConst.CONTINUE_WORDS[0] in rsp.lower()
        else:
            confirmed = rsp.lower().startswith("confirm")

        logger.info(f"Ask Review Result: `{rsp}` for above phase.")
        return rsp, confirmed
