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
from metagpt.utils.report import ThoughtReporter


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
        # Command.PUBLISH_MESSAGE,
        Command.ASK_HUMAN,
        Command.REPLY_TO_HUMAN,
        # Command.PASS,
    ]
    commands: list[dict] = []  # issued commands to be executed
    user_requirement: str = ""

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

        plan_status = self.planner.plan.model_dump(include=["goal", "tasks"])
        # for task in plan_status["tasks"]:
        #     task.pop("code")
        #     task.pop("result")
        prompt = CMD_PROMPT.format(
            plan_status=plan_status,
            example=example,
            available_commands=prepare_command_prompt(self.available_commands),
        )
        context = self.llm.format_msg(self.working_memory.get() + [Message(content=prompt, role="user")])
        # print(*context, sep="\n" + "*" * 5 + "\n")
        async with ThoughtReporter(enable_llm_stream=True):
            rsp = await self.llm.aask(context)
        self.commands = json.loads(CodeParser.parse_code(block=None, text=rsp))
        self.rc.working_memory.add(Message(content=rsp, role="assistant"))

        await run_commands(self, self.commands, self.rc.working_memory)

        return bool(self.rc.todo)

    async def _act(self) -> Message:
        """Useful in 'react' mode. Return a Message conforming to Role._act interface."""
        logger.info(f"ready to take on task {self.planner.plan.current_task}")

        # TODO: Consider an appropriate location to insert task experience formally
        experience = KeywordExpRetriever().retrieve(self.planner.plan.current_task.instruction, exp_type="task")
        if experience and experience not in [msg.content for msg in self.rc.working_memory.get()]:
            exp_msg = Message(content=experience, role="assistant")
            self.rc.working_memory.add(exp_msg)

        code, result, is_success = await self._write_and_exec_code()
        self.planner.plan.current_task.is_success = (
            is_success  # mark is_success, determine is_finished later in thinking
        )

        # FIXME: task result is always overwritten by the last act, whereas it can be made of of multiple acts
        self.task_result = TaskResult(code=code, result=result, is_success=is_success)
        return Message(content="Task completed", role="assistant", sent_from=self._setting, cause_by=WriteAnalysisCode)

    async def _react(self) -> Message:
        # NOTE: Diff 1: Each time landing here means observing news, set todo to allow news processing in _think
        self._set_state(0)

        actions_taken = 0
        rsp = Message(content="No actions taken yet", cause_by=Action)  # will be overwritten after Role _act
        while actions_taken < self.rc.max_react_loop:
            # NOTE: Diff 2: Keep observing within _react, news will go into memory, allowing adapting to new info
            # add news from self._observe, the one called in self.run, consider removing when switching from working_memory to memory
            self.working_memory.add_batch(self.rc.news)
            await self._observe()
            # add news from this self._observe, we need twice because _observe rewrites rc.news
            self.working_memory.add_batch(self.rc.news)

            # think
            has_todo = await self._think()
            if not has_todo:
                break
            # act
            logger.debug(f"{self._setting}: {self.rc.state=}, will do {self.rc.todo}")
            rsp = await self._act()
            actions_taken += 1
        return rsp  # return output from the last action
