from __future__ import annotations

import json

from pydantic import model_validator

from metagpt.actions.di.run_command import RunCommand
from metagpt.prompts.di.team_leader import (
    CMD_PROMPT,
    FINISH_CURRENT_TASK_CMD,
    SYSTEM_PROMPT,
)
from metagpt.roles import Role
from metagpt.schema import Message, TaskResult
from metagpt.strategy.experience_retriever import SimpleExpRetriever
from metagpt.strategy.planner import Planner
from metagpt.strategy.thinking_command import (
    Command,
    prepare_command_prompt,
    run_commands,
)
from metagpt.utils.common import CodeParser


class TeamLeader(Role):
    name: str = "Tim"
    profile: str = "Team Leader"
    task_result: TaskResult = None
    available_commands: list[Command] = [
        Command.APPEND_TASK,
        Command.RESET_TASK,
        Command.REPLACE_TASK,
        Command.FINISH_CURRENT_TASK,
        Command.PUBLISH_MESSAGE,
        Command.ASK_HUMAN,
        Command.REPLY_TO_HUMAN,
        Command.PASS,
    ]
    commands: list[dict] = []  # issued commands to be executed

    @model_validator(mode="after")
    def set_plan(self) -> "TeamLeader":
        self.rc.working_memory = (
            self.rc.memory
        )  # TeamLeader does not need working memory, all messages should go into memory
        self.planner = Planner(goal=self.goal, working_memory=self.rc.working_memory, auto_run=True)
        return self

    async def _think(self) -> bool:
        """Useful in 'react' mode. Use LLM to decide whether and what to do next."""

        if not self.planner.plan.goal:
            user_requirement = self.get_memories()[-1].content
            self.planner.plan.goal = user_requirement

        plan_status = self.planner.plan.model_dump(include=["goal", "tasks"])
        for task in plan_status["tasks"]:
            task.pop("code")
            task.pop("result")
        team_info = ""
        for role in self.rc.env.roles.values():
            if role.profile == "TeamLeader":
                continue
            team_info += f"{role.name}: {role.profile}, {role.goal}\n"
        example = SimpleExpRetriever().retrieve()

        prompt = CMD_PROMPT.format(
            plan_status=plan_status,
            team_info=team_info,
            example=example,
            available_commands=prepare_command_prompt(self.available_commands),
        )
        context = self.llm.format_msg(self.get_memories(k=10) + [Message(content=prompt, role="user")])

        rsp = await self.llm.aask(context, system_msgs=[SYSTEM_PROMPT])
        self.commands = json.loads(CodeParser.parse_code(block=None, text=rsp))
        self.rc.memory.add(Message(content=rsp, role="assistant"))

        return True

    async def _act(self) -> Message:
        """Useful in 'react' mode. Return a Message conforming to Role._act interface."""
        await run_commands(self, self.commands)
        self.task_result = TaskResult(result="Success", is_success=True)
        msg = Message(content="Commands executed", send_to="no one")  # a dummy message to conform to the interface
        self.rc.memory.add(msg)
        return msg

    def publish_message(self, msg):
        """If the role belongs to env, then the role's messages will be broadcast to env"""
        if not msg:
            return
        if not self.rc.env:
            # If env does not exist, do not publish the message
            return
        msg.sent_from = self.profile
        msg.cause_by = RunCommand
        self.rc.env.publish_message(msg, publicer=self.profile)

    def finish_current_task(self):
        self.planner.plan.finish_current_task()
        self.rc.memory.add(Message(content=FINISH_CURRENT_TASK_CMD, role="assistant"))
