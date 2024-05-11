from __future__ import annotations

import json
from typing import Literal

from pydantic import model_validator

from metagpt.actions import Action
from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.logs import logger
from metagpt.prompts.di.data_analyst import CMD_PROMPT
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import Message, TaskResult
from metagpt.strategy.experience_retriever import KeywordExpRetriever
from metagpt.strategy.planner import Planner
from metagpt.strategy.thinking_command import (
    Command,
    prepare_command_prompt,
    run_commands,
)
from metagpt.tools.tool_recommend import BM25ToolRecommender
from metagpt.utils.common import CodeParser


class DataAnalyst(DataInterpreter):
    name: str = "David"
    profile: str = "DataAnalyst"
    goal: str = "Take on any data-related tasks, such as data analysis, machine learning, deep learning, web browsing, web scraping, web searching, web deployment, terminal operation, git and github operation, etc."
    react_mode: Literal["react"] = "react"
    max_react_loop: int = 20  # used for react mode
    task_result: TaskResult = None
    available_commands: list[Command] = [
        Command.APPEND_TASK,
        Command.RESET_TASK,
        Command.REPLACE_TASK,
        Command.FINISH_CURRENT_TASK,
        Command.CONTINUE_WITH_CURRENT_TASK,
        # Command.PUBLISH_MESSAGE,
        Command.ASK_HUMAN,
        Command.REPLY_TO_HUMAN,
        # Command.PASS,
    ]
    commands: list[dict] = []  # issued commands to be executed

    @model_validator(mode="after")
    def set_plan_and_tool(self) -> "DataInterpreter":
        # We force using this parameter for DataAnalyst
        assert self.react_mode == "react"
        assert self.auto_run
        assert self.use_plan

        # Roughly the same part as DataInterpreter.set_plan_and_tool
        self._set_react_mode(react_mode=self.react_mode, max_react_loop=self.max_react_loop, auto_run=self.auto_run)
        if self.tools and not self.tool_recommender:
            self.tool_recommender = BM25ToolRecommender(tools=self.tools)
        self.set_actions([WriteAnalysisCode])
        self._set_state(0)

        # HACK: Init Planner, control it through dynamic thinking; Consider formalizing as a react mode
        self.planner = Planner(goal="", working_memory=self.rc.working_memory, auto_run=True)

        return self

    async def _think(self) -> bool:
        """Useful in 'react' mode. Use LLM to decide whether and what to do next."""
        self._set_state(0)
        example = ""
        if not self.planner.plan.goal:
            self.user_requirement = self.get_memories()[-1].content
            self.planner.plan.goal = self.user_requirement
            example = KeywordExpRetriever().retrieve(self.user_requirement)
        else:
            self.working_memory.add_batch(self.rc.news)
            context = "\n\n".join([str(mem) for mem in self.working_memory.get()])
            example = KeywordExpRetriever().retrieve(context)

        plan_status = self.planner.plan.model_dump(include=["goal", "tasks"])
        for task in plan_status["tasks"]:
            task.pop("code")
            task.pop("result")
            task.pop("is_success")
        prompt = CMD_PROMPT.format(
            plan_status=plan_status,
            example=example,
            available_commands=prepare_command_prompt(self.available_commands),
        )
        context = self.llm.format_msg(self.working_memory.get() + [Message(content=prompt, role="user")])

        rsp = await self.llm.aask(context)
        self.commands = json.loads(CodeParser.parse_code(block=None, text=rsp))
        self.rc.memory.add(Message(content=rsp, role="assistant"))

        await run_commands(self, self.commands, self.rc.working_memory)

        return bool(self.rc.todo)

    async def _act(self) -> Message:
        """Useful in 'react' mode. Return a Message conforming to Role._act interface."""
        logger.info(f"ready to take on task {self.planner.plan.current_task}")
        code, result, is_success = await self._write_and_exec_code()
        self.planner.plan.current_task.is_success = (
            is_success  # mark is_success, determine is_finished later in thinking
        )

        # FIXME: task result is always overwritten by the last act, whereas it can be made of of multiple acts
        self.task_result = TaskResult(code=code, result=result, is_success=is_success)
        return Message(content="Task completed", role="assistant", sent_from=self._setting, cause_by=WriteAnalysisCode)

    async def _react(self) -> Message:
        actions_taken = 0
        rsp = Message(content="No actions taken yet", cause_by=Action)  # will be overwritten after Role _act
        while actions_taken < self.rc.max_react_loop:
            # NOTE: difference here, keep observing within react
            await self._observe()
            # think
            has_todo = await self._think()
            if not has_todo:
                break
            # act
            logger.debug(f"{self._setting}: {self.rc.state=}, will do {self.rc.todo}")
            rsp = await self._act()
            actions_taken += 1
        return rsp  # return output from the last action
