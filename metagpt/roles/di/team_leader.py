from __future__ import annotations

import json

from pydantic import model_validator

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.prompts.di.team_leader import (
    PLANNING_CMD_PROMPT,
    ROUTING_CMD_PROMPT,
    prepare_command_prompt,
)
from metagpt.roles import Role
from metagpt.schema import Message, Task, TaskResult
from metagpt.strategy.experience_retriever import SimplePlanningExpRetriever
from metagpt.strategy.planner import Planner
from metagpt.strategy.thinking_command import Command
from metagpt.utils.common import CodeParser


class TeamLeader(Role):
    name: str = "Tim"
    profile: str = "Team Leader"
    task_result: TaskResult = None
    planning_commands: list[Command] = [
        Command.APPEND_TASK,
        Command.RESET_TASK,
        Command.REPLACE_TASK,
        Command.FINISH_CURRENT_TASK,
        Command.REPLY_TO_HUMAN,
        Command.PASS,
    ]
    env_commands: list[Command] = [
        Command.PUBLISH_MESSAGE,
        Command.ASK_HUMAN,
        Command.REPLY_TO_HUMAN,
        Command.PASS,
    ]

    @model_validator(mode="after")
    def set_plan(self) -> "TeamLeader":
        self.planner = Planner(goal=self.goal, working_memory=self.rc.working_memory, auto_run=True)
        return self

    def _run_env_command(self, cmd):
        assert isinstance(self.rc.env, MGXEnv), "TeamLeader should only be used in an MGXEnv"
        if cmd["command_name"] == Command.PUBLISH_MESSAGE.cmd_name:
            self.rc.env.publish_message(Message(**cmd["args"]), publicer=self.profile)
        elif cmd["command_name"] == Command.ASK_HUMAN.cmd_name:
            self.rc.env.ask_human(**cmd["args"])
        elif cmd["command_name"] == Command.REPLY_TO_HUMAN.cmd_name:
            self.rc.env.reply_to_human(**cmd["args"])

    def _run_internal_command(self, cmd):
        if cmd["command_name"] == Command.APPEND_TASK.cmd_name:
            self.planner.plan.append_task(Task(**cmd["args"]))
        elif cmd["command_name"] == Command.RESET_TASK.cmd_name:
            self.planner.plan.reset_task(**cmd["args"])
        elif cmd["command_name"] == Command.REPLACE_TASK.cmd_name:
            self.planner.plan.replace_task(Task(**cmd["args"]))
        elif cmd["command_name"] == Command.FINISH_CURRENT_TASK.cmd_name:
            self.planner.plan.current_task.update_task_result(task_result=self.task_result)
            self.planner.plan.finish_current_task()
            self.rc.working_memory.clear()

    def run_commands(self, cmds):
        print(*cmds, sep="\n")
        for cmd in cmds:
            self._run_env_command(cmd)
            self._run_internal_command(cmd)

        if self.planner.plan.is_plan_finished():
            self._set_state(-1)

    def get_memory(self) -> list[Message]:
        mem = self.rc.memory.get()
        for m in mem:
            if m.role not in ["system", "user", "assistant"]:
                m.content = f"from {m.role} to {m.send_to}: {m.content}"
                m.role = "assistant"
        return mem

    async def _think(self) -> bool:
        """Useful in 'react' mode. Use LLM to decide whether and what to do next."""
        self.commands = []

        example = ""
        if not self.planner.plan.goal:
            user_requirement = self.get_memories()[-1].content
            self.planner.plan.goal = user_requirement
            example = SimplePlanningExpRetriever().retrieve()

        # common info
        team_info = ""
        for role in self.rc.env.roles.values():
            if role.profile == "TeamLeader":
                continue
            team_info += f"{role.name}: {role.profile}, {role.goal}\n"
        # print(team_info)

        # plan commands
        plan_status = self.planner.plan.model_dump(include=["goal", "tasks"])
        for task in plan_status["tasks"]:
            task.pop("code")
            task.pop("result")
        plan_prompt = PLANNING_CMD_PROMPT.format(
            plan_status=plan_status,
            team_info=team_info,
            example=example,
            available_commands=prepare_command_prompt(self.planning_commands),
        )
        context = self.llm.format_msg(self.get_memory() + [Message(content=plan_prompt, role="user")])

        plan_rsp = await self.llm.aask(context)
        plan_rsp_dict = json.loads(CodeParser.parse_code(block=None, text=plan_rsp))
        self.commands.extend(plan_rsp_dict)
        self.rc.memory.add(Message(content=plan_rsp, role="assistant"))

        # routing commands
        route_prompt = ROUTING_CMD_PROMPT.format(
            plan_status=plan_status,
            team_info=team_info,
            example="",
            available_commands=prepare_command_prompt(self.env_commands),
        )
        context = self.llm.format_msg(self.get_memory() + [Message(content=route_prompt, role="user")])

        route_rsp = await self.llm.aask(context)
        route_rsp_dict = json.loads(CodeParser.parse_code(block=None, text=route_rsp))
        self.commands.extend(route_rsp_dict)
        self.rc.memory.add(Message(content=route_rsp, role="assistant"))

        return True

    async def _act(self) -> Message:
        """Useful in 'react' mode. Return a Message conforming to Role._act interface."""
        self.run_commands(self.commands)
        self.task_result = TaskResult(result="Success", is_success=True)
        return Message(content="Commands executed", role="assistant")
