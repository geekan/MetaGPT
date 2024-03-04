from __future__ import annotations

from typing import Literal, Tuple

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message, Plan
from metagpt.utils.common import CodeParser


class ReviewConst:
    TASK_REVIEW_TRIGGER = "task"
    CODE_REVIEW_TRIGGER = "code"
    CONTINUE_WORDS = ["confirm", "continue", "c", "yes", "y"]
    CHANGE_WORDS = ["change"]
    EXIT_WORDS = ["exit"]
    TASK_REVIEW_INSTRUCTION = (
        f"If you want to change, add, delete a task or merge tasks in the plan, type '{CHANGE_WORDS[0]} task task_id or current task, ... (things to change)' "
        f"If you confirm the output from the current task and wish to continue, type: {CONTINUE_WORDS[0]}"
    )
    CODE_REVIEW_INSTRUCTION = (
        f"If you want the codes to be rewritten, type '{CHANGE_WORDS[0]} ... (your change advice)' "
        f"If you want to leave it as is, type: {CONTINUE_WORDS[0]} or {CONTINUE_WORDS[1]}"
    )
    EXIT_INSTRUCTION = f"If you want to terminate the process, type: {EXIT_WORDS[0]}"


class AskReview(Action):
    async def run(
        self,
        context: list[Message] = [],
        plan: Plan = None,
        trigger: str = ReviewConst.TASK_REVIEW_TRIGGER,
        review_type: Literal["human", "llm", "confirm_all"] = "human",
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
        review_instruction = (
            ReviewConst.TASK_REVIEW_INSTRUCTION
            if trigger == ReviewConst.TASK_REVIEW_TRIGGER
            else ReviewConst.CODE_REVIEW_INSTRUCTION
        )
        prompt = (
            f"This is a <{trigger}> review. Please review output from {latest_action}\n"
            f"{review_instruction}\n"
            f"{ReviewConst.EXIT_INSTRUCTION}\n"
            "Please type your review below:\n"
        )

        if review_type == "human":
            rsp = input(prompt)
        elif review_type == "llm":
            sys_msg = [
                f"You are very good at reviewing *code*, {review_instruction}",
                "you will get the *current task* and *code execution results*.",
                "Please give sound suggestions to improve the effectiveness of the current task.",
                "Dont return code, just suggestionsjust like the follwing with three backquote ```:",
                f"```\n{ReviewConst.CHANGE_WORDS[0]} ... (your change advice).\n```",
                "```\nconfirm\n```",
                "```\nredo, (reason for re-executing the task)\n```",
                "```\nexit\n```",
                "**Notice: The starting word in your suggestions must be one of the following: ",
                f"{ReviewConst.CHANGE_WORDS[0]}, confirm, redo**",
            ]
            review_msg = "\n".join([str(c) for c in context])
            _rsp = await self.llm.aask(msg=review_msg, system_msgs=sys_msg)
            rsp = CodeParser.parse_code(None, _rsp)
            rsp = rsp[:-1] if rsp.endswith("\n") else rsp
        else:
            rsp = "confirm"

        if rsp.lower() in ReviewConst.EXIT_WORDS:
            exit()

        # Confirmation can be one of "confirm", "continue", "c", "yes", "y" exactly, or sentences containing "confirm".
        # One could say "confirm this task, but change the next task to ..."
        confirmed = rsp.lower() in ReviewConst.CONTINUE_WORDS or ReviewConst.CONTINUE_WORDS[0] in rsp.lower()

        logger.info(f"Ask Review Result: `{rsp}` for above phase.")
        return rsp, confirmed
