import json
from typing import Dict, List, Union

from metagpt.actions import Action
from metagpt.schema import Message, Plan
from metagpt.logs import logger


def truncate(result: str, keep_len: int = 1000) -> str:
    desc = "Truncated to show only the last 1000 characters\n"
    if result.startswith(desc):
        result = result[-len(desc) :]

    if len(result) > keep_len:
        result = result[-keep_len:]

    if not result.startswith(desc):
        return desc + result
    return desc


class ReviewConst:
    TASK_REVIEW_TRIGGER = "task"
    CODE_REVIEW_TRIGGER = "code"
    CONTINUE_WORD = ["confirm", "continue", "c", "yes", "y"]
    CHANGE_WORD = ["change"]
    EXIT_WORD = ["exit"]
    TASK_REVIEW_INSTRUCTION = (
        f"If you want to change, add, delete a task or merge tasks in the plan, say '{CHANGE_WORD[0]} task task_id or current task, ... (things to change)' "
        f"If you confirm the output from the current task and wish to continue, type: {CONTINUE_WORD[0]}"
    )
    CODE_REVIEW_INSTRUCTION = (
        f"If you want the codes to be rewritten, say '{CHANGE_WORD[0]} ... (your change advice)' "
        f"If you want to leave it as is, type: {CONTINUE_WORD[0]} or {CONTINUE_WORD[1]}"
    )
    EXIT_INSTRUCTION = f"If you want to terminate the process, type: {EXIT_WORD[0]}"


class AskReview(Action):
    async def run(
        self, context: List[Message], plan: Plan = None, trigger: str = "task"
    ):
        logger.info("Current overall plan:")
        logger.info(
            "\n".join(
                [
                    f"{task.task_id}: {task.instruction}, is_finished: {task.is_finished}"
                    for task in plan.tasks
                ]
            )
        )

        logger.info("most recent context:")
        latest_action = context[-1].cause_by.__name__ if context[-1].cause_by else ""
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

        rsp = input(prompt)

        if rsp.lower() in ReviewConst.EXIT_WORD:
            exit()

        confirmed = rsp.lower() in ReviewConst.CONTINUE_WORD

        return rsp, confirmed


class SummarizeAnalysis(Action):
    PROMPT_TEMPLATE = """
    # Context
    {context}
    # Summary
    Output a 30-word summary on analysis tool and modeling algorithms you have used, and the corresponding result. Make sure to announce the complete path to your test prediction file. Your summary:
    """

    def __init__(self, name: str = "", context=None, llm=None) -> str:
        super().__init__(name, context, llm)

    async def run(self, conmpleted_plan: Plan) -> str:
        tasks = json.dumps(
            [task.dict() for task in conmpleted_plan.tasks],
            indent=4,
            ensure_ascii=False,
        )  # all tasks finished, return all task outputs
        prompt = self.PROMPT_TEMPLATE.format(context=tasks)
        summary = await self._aask(prompt)
        return summary


class Reflect(Action):
    PROMPT_TEMPLATE = """
    # User Requirement
    {user_requirement}
    # Context
    {context}
    # Summary
    Above is all your attempts to tackle the user requirement. You plan, act, submit your output, and get the result and feedback.
    First, summarize each of your previous trial in a triple of (your methods, the corresponding result, potential improvement), list them out.
    # Takeaways
    Second, carefully find key takeaways from your summarization in a step-by-step thinking process
    # Guidance
    Finally, make a concise one-sentence guidance for improving your future plan.
    Your response:
    """

    async def run(self, context: str) -> str:
        user_requirement = "Score as high as possible in a data modeling competition"
        prompt = self.PROMPT_TEMPLATE.format(context=context, user_requirement=user_requirement)
        rsp = await self._aask(prompt)
        return rsp
