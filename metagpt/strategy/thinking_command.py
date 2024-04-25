from enum import Enum

from pydantic import BaseModel


class CommandDef(BaseModel):
    name: str
    signature: str = ""
    desc: str = ""


class Command(Enum):
    # commands for planning
    APPEND_TASK = CommandDef(
        name="append_task",
        signature="append_task(task_id: str, dependent_task_ids: list[str], instruction: str, assignee: str)",
        desc="Append a new task with task_id (number) to the end of existing task sequences. If dependent_task_ids is not empty, the task will depend on the tasks with the ids in the list.",
    )
    RESET_TASK = CommandDef(
        name="reset_task",
        signature="reset_task(task_id: str)",
        desc="Reset a task based on task_id, i.e. set Task.is_finished=False and request redo. This also resets all tasks depending on it.",
    )
    REPLACE_TASK = CommandDef(
        name="replace_task",
        signature="replace_task(task_id: str, new_dependent_task_ids: list[str], new_instruction: str, new_assignee: str)",
        desc="Replace an existing task (can be current task) based on task_id, and reset all tasks depending on it.",
    )
    FINISH_CURRENT_TASK = CommandDef(
        name="finish_current_task",
        signature="finish_current_task()",
        desc="Finishes current task, set Task.is_finished=True, set current task to next task",
    )

    # commands for env interaction
    PUBLISH_MESSAGE = CommandDef(
        name="publish_message",
        signature="publish_message(content: str, send_to: str)",
        desc="Publish a message to a team member, use member name to fill send_to args. You may copy the full original content or add additional information from upstream. This will make team members start their work. DONT omit any necessary info such as path, link, environment from original content to team members because you are their sole info source. However, if the original content is long or contains concrete info, you should forward the message using forward_message instead of publishing it.",
    )
    REPLY_TO_HUMAN = CommandDef(
        name="reply_to_human",
        signature="reply_to_human(content: str)",
        desc="Reply to human user with the content provided. Use this when you have a clear answer or solution to the user's question.",
    )
    ASK_HUMAN = CommandDef(
        name="ask_human",
        signature="ask_human(question: str)",
        desc="Use this when you fail the current task or if you are unsure of the situation encountered. Your response should contain a brief summary of your situation, ended with a clear and concise question.",
    )

    # common commands
    PASS = CommandDef(
        name="pass",
        signature="pass",
        desc="Pass and do nothing, if you don't think the plan needs to be updated nor a message to be published or forwarded. The reasons can be the latest message is unnecessary or obsolete, or you want to wait for more information before making a move.",
    )

    @property
    def cmd_name(self):
        return self.value.name
