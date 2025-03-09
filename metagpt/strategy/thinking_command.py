from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.memory import Memory
from metagpt.roles import Role
from metagpt.schema import Message


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
        desc="Publish a message to a team member, use member name to fill send_to args. You may copy the full original content or add additional information from upstream. This will make team members start their work. DONT omit any necessary info such as path, link, environment, programming language, framework, requirement, constraint from original content to team members because you are their sole info source.",
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


def prepare_command_prompt(commands: list[Command]) -> str:
    command_prompt = ""
    for i, command in enumerate(commands):
        command_prompt += f"{i+1}. {command.value.signature}:\n{command.value.desc}\n\n"
    return command_prompt


async def run_env_command(role: Role, cmd: list[dict], role_memory: Memory = None):
    if not isinstance(role.rc.env, MGXEnv):
        return
    if cmd["command_name"] == Command.PUBLISH_MESSAGE.cmd_name:
        role.publish_message(Message(**cmd["args"]))
    if cmd["command_name"] == Command.ASK_HUMAN.cmd_name:
        # TODO: Operation on role memory should not appear here, consider moving it into role
        role.rc.working_memory.add(Message(content=cmd["args"]["question"], role="assistant"))
        human_rsp = await role.rc.env.ask_human(sent_from=role, **cmd["args"])
        role.rc.working_memory.add(Message(content=human_rsp, role="user"))
    elif cmd["command_name"] == Command.REPLY_TO_HUMAN.cmd_name:
        # TODO: consider if the message should go into memory
        await role.rc.env.reply_to_human(sent_from=role, **cmd["args"])


def run_plan_command(role: Role, cmd: list[dict]):
    if cmd["command_name"] == Command.APPEND_TASK.cmd_name:
        role.planner.plan.append_task(**cmd["args"])
    elif cmd["command_name"] == Command.RESET_TASK.cmd_name:
        role.planner.plan.reset_task(**cmd["args"])
    elif cmd["command_name"] == Command.REPLACE_TASK.cmd_name:
        role.planner.plan.replace_task(**cmd["args"])
    elif cmd["command_name"] == Command.FINISH_CURRENT_TASK.cmd_name:
        if role.planner.plan.is_plan_finished():
            return
        if role.task_result:
            role.planner.plan.current_task.update_task_result(task_result=role.task_result)
        role.planner.plan.finish_current_task()
        role.rc.working_memory.clear()


async def run_commands(role: Role, cmds: list[dict], role_memory: Memory = None):
    print(*cmds, sep="\n")
    for cmd in cmds:
        await run_env_command(role, cmd, role_memory)
        run_plan_command(role, cmd)

    if role.planner.plan.is_plan_finished():
        role._set_state(-1)
