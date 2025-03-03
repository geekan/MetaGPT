from __future__ import annotations

from typing import Annotated

from pydantic import Field

from metagpt.actions.di.run_command import RunCommand
from metagpt.const import TEAMLEADER_NAME
from metagpt.prompts.di.role_zero import QUICK_THINK_TAG
from metagpt.prompts.di.team_leader import (
    FINISH_CURRENT_TASK_CMD,
    TL_INFO,
    TL_INSTRUCTION,
    TL_THOUGHT_GUIDANCE,
)
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import AIMessage, Message, UserMessage
from metagpt.strategy.experience_retriever import ExpRetriever, SimpleExpRetriever
from metagpt.tools.tool_registry import register_tool


@register_tool(include_functions=["publish_team_message"])
class TeamLeader(RoleZero):
    name: str = TEAMLEADER_NAME
    profile: str = "Team Leader"
    goal: str = "Manage a team to assist users"
    thought_guidance: str = TL_THOUGHT_GUIDANCE
    # TeamLeader only reacts once each time, but may encounter errors or need to ask human, thus allowing 2 more turns
    max_react_loop: int = 3

    tools: list[str] = ["Plan", "RoleZero", "TeamLeader"]

    experience_retriever: Annotated[ExpRetriever, Field(exclude=True)] = SimpleExpRetriever()

    use_summary: bool = False

    def _update_tool_execution(self):
        self.tool_execution_map.update(
            {
                "TeamLeader.publish_team_message": self.publish_team_message,
                "TeamLeader.publish_message": self.publish_team_message,  # alias
            }
        )

    def _get_team_info(self) -> str:
        if not self.rc.env:
            return ""
        team_info = ""
        for role in self.rc.env.roles.values():
            # if role.profile == "Team Leader":
            #     continue
            team_info += f"{role.name}: {role.profile}, {role.goal}\n"
        return team_info

    def _get_prefix(self) -> str:
        role_info = super()._get_prefix()
        team_info = self._get_team_info()
        return TL_INFO.format(role_info=role_info, team_info=team_info)

    async def _think(self) -> bool:
        self.instruction = TL_INSTRUCTION.format(team_info=self._get_team_info())
        return await super()._think()

    def publish_message(self, msg: Message, send_to="no one"):
        """Overwrite Role.publish_message, send to no one if called within Role.run (except for quick think), send to the specified role if called dynamically."""
        if not msg:
            return
        if not self.rc.env:
            # If env does not exist, do not publish the message
            return
        if msg.cause_by != QUICK_THINK_TAG:
            msg.send_to = send_to
        self.rc.env.publish_message(msg, publicer=self.profile)

    def publish_team_message(self, content: str, send_to: str):
        """
        Publish a message to a team member, use member name to fill send_to args. You may copy the full original content or add additional information from upstream. This will make team members start their work.
        DONT omit any necessary info such as path, link, environment, programming language, framework, requirement, constraint from original content to team members because you are their sole info source.
        """
        self._set_state(-1)  # each time publishing a message, pause to wait for the response
        if send_to == self.name:
            return  # Avoid sending message to self
        # Specify the outer send_to to overwrite the default "no one" value. Use UserMessage because message from self is like a user request for others.
        self.publish_message(
            UserMessage(content=content, sent_from=self.name, send_to=send_to, cause_by=RunCommand), send_to=send_to
        )

    def finish_current_task(self):
        self.planner.plan.finish_current_task()
        self.rc.memory.add(AIMessage(content=FINISH_CURRENT_TASK_CMD))
