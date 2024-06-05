from __future__ import annotations

from pydantic import model_validator

from metagpt.actions.di.run_command import RunCommand
from metagpt.prompts.di.team_leader import (
    FINISH_CURRENT_TASK_CMD,
    SYSTEM_PROMPT,
    TL_INSTRUCTION,
)
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import AIMessage, Message, UserMessage
from metagpt.strategy.experience_retriever import ExpRetriever, SimpleExpRetriever
from metagpt.tools.tool_registry import register_tool


@register_tool(include_functions=["publish_team_message"])
class TeamLeader(RoleZero):
    name: str = "Tim"
    profile: str = "Team Leader"
    system_msg: list[str] = [SYSTEM_PROMPT]

    max_react_loop: int = 1  # TeamLeader only reacts once each time

    tools: list[str] = ["Plan", "RoleZero", "TeamLeader"]

    experience_retriever: ExpRetriever = SimpleExpRetriever()

    @model_validator(mode="after")
    def set_tool_execution(self) -> "RoleZero":
        self.tool_execution_map = {
            "Plan.append_task": self.planner.plan.append_task,
            "Plan.reset_task": self.planner.plan.reset_task,
            "Plan.replace_task": self.planner.plan.replace_task,
            "RoleZero.ask_human": self.ask_human,
            "RoleZero.reply_to_human": self.reply_to_human,
            "TeamLeader.publish_team_message": self.publish_team_message,
        }
        return self

    def set_instruction(self):
        team_info = ""
        for role in self.rc.env.roles.values():
            # if role.profile == "Team Leader":
            #     continue
            team_info += f"{role.name}: {role.profile}, {role.goal}\n"
        self.instruction = TL_INSTRUCTION.format(team_info=team_info)

    async def _think(self) -> bool:
        self.set_instruction()
        return await super()._think()

    def publish_message(self, msg: Message, send_to="no one"):
        """Overwrite Role.publish_message, send to no one if called within Role.run, send to the specified role if called dynamically."""
        if not msg:
            return
        if not self.rc.env:
            # If env does not exist, do not publish the message
            return
        msg.send_to = send_to
        self.rc.env.publish_message(msg, publicer=self.profile)

    def publish_team_message(self, content: str, send_to: str):
        """
        Publish a message to a team member, use member name to fill send_to args. You may copy the full original content or add additional information from upstream. This will make team members start their work.
        DONT omit any necessary info such as path, link, environment, programming language, framework, requirement, constraint from original content to team members because you are their sole info source.
        """
        # Specify the outer send_to to overwrite the default "no one" value. Use UserMessage because message from self is like a user request for others.
        self.publish_message(
            UserMessage(content=content, sent_from=self.name, send_to=send_to, cause_by=RunCommand), send_to=send_to
        )

    def finish_current_task(self):
        self.planner.plan.finish_current_task()
        self.rc.memory.add(AIMessage(content=FINISH_CURRENT_TASK_CMD))
