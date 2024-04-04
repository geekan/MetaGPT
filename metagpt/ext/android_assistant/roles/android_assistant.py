#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : android assistant to learn from app operations and operate apps
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import Field

from metagpt.actions.add_requirement import UserRequirement
from metagpt.config2 import config
from metagpt.const import EXAMPLE_PATH
from metagpt.ext.android_assistant.actions.manual_record import ManualRecord
from metagpt.ext.android_assistant.actions.parse_record import ParseRecord
from metagpt.ext.android_assistant.actions.screenshot_parse import ScreenshotParse
from metagpt.ext.android_assistant.actions.self_learn_and_reflect import (
    SelfLearnAndReflect,
)
from metagpt.ext.android_assistant.utils.schema import AndroidActionOutput, RunState
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message


class AndroidAssistant(Role):
    name: str = "Nick"
    profile: str = "AndroidAssistant"
    goal: str = "operate the mobile phone's apps with self-learn"

    task_desc: str = ""
    round_count: int = 0
    last_act: str = "None"
    output_root_dir: Optional[Path] = Field(default=None)
    task_dir: Optional[Path] = Field(default=None)
    docs_dir: Optional[Path] = Field(default=None)
    grid_on: bool = Field(default=False)

    def __init__(self, **data):
        super().__init__(**data)

        self._watch([UserRequirement, AndroidActionOutput])
        extra_config = config.extra
        self.task_desc = extra_config.get("task_desc", "Just explore any app in this phone!")
        app_name = extra_config.get("app_name", "demo")
        data_dir = self.output_root_dir.absolute().joinpath("output") or EXAMPLE_PATH.joinpath(
            "android_assistant/output"
        )
        cur_datetime = datetime.fromtimestamp(int(time.time())).strftime("%Y-%m-%d_%H-%M-%S")

        """Firstly, we decide the state with user config, further, we can do it automatically, like if it's new app,
        run the learn first and then do the act stage or learn it during the action.
        """
        stage = extra_config.get("stage")
        mode = extra_config.get("mode")
        if stage == "learn" and mode == "manual":
            # choose ManualRecord and then run ParseRecord
            # Remember, only run each action only one time, no need to run n_round.
            self.set_actions([ManualRecord, ParseRecord])
            self.task_dir = data_dir.joinpath(app_name, f"manual_learn_{cur_datetime}")
            self.docs_dir = data_dir.joinpath(app_name, "manual_docs")
        elif stage == "learn" and mode == "auto":
            # choose SelfLearnAndReflect to run
            self.set_actions([SelfLearnAndReflect])
            self.task_dir = data_dir.joinpath(app_name, f"auto_learn_{cur_datetime}")
            self.docs_dir = data_dir.joinpath(app_name, "auto_docs")
        elif stage == "act":
            # choose ScreenshotParse to run
            self.set_actions([ScreenshotParse])
            self.task_dir = data_dir.joinpath(app_name, f"act_{cur_datetime}")
            if mode == "manual":
                self.docs_dir = data_dir.joinpath(app_name, "manual_docs")
            else:
                self.docs_dir = data_dir.joinpath(app_name, "auto_docs")
        else:
            raise ValueError(f"invalid stage: {stage}, mode: {mode}")

        self._check_dir()

        self._set_react_mode(RoleReactMode.BY_ORDER)

    def _check_dir(self):
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    async def react(self) -> Message:
        self.round_count += 1
        result = await super().react()
        logger.debug(f"react result {result}")
        return result

    async def _observe(self, ignore_memory=True) -> int:
        """ignore old memory to make it run multi rounds inside a role"""
        newest_msgs = self.rc.memory.get(k=1)
        newest_msg = newest_msgs[0] if newest_msgs else None
        if newest_msg and (RunState.SUCCESS.value.upper() not in newest_msg.content):
            ignore_memory = False
            state_val = newest_msg.content.split(".")[-1]  # RoundCount: 1, action_state: RunState.SUCCESS
            logger.warning(f"Latest action_state is {state_val}, will run in the remainder rounds without `react`")
        return await super()._observe(ignore_memory)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        if isinstance(todo, ManualRecord):
            resp = await todo.run(task_dir=self.task_dir, task_desc=self.task_desc, env=self.rc.env)
        elif isinstance(todo, ParseRecord):
            resp = await todo.run(
                task_dir=self.task_dir,
                docs_dir=self.docs_dir,
            )
        elif isinstance(todo, SelfLearnAndReflect):
            resp = await todo.run(
                round_count=self.round_count,
                task_desc=self.task_desc,
                last_act=self.last_act,
                task_dir=self.task_dir,
                docs_dir=self.docs_dir,
                env=self.rc.env,
            )
            if resp.action_state == RunState.SUCCESS:
                self.last_act = resp.data.get("last_act")
        elif isinstance(todo, ScreenshotParse):
            resp = await todo.run(
                round_count=self.round_count,
                task_desc=self.task_desc,
                last_act=self.last_act,
                task_dir=self.task_dir,
                docs_dir=self.docs_dir,
                grid_on=self.grid_on,
                env=self.rc.env,
            )
            if resp.action_state == RunState.SUCCESS:
                logger.info(f"grid_on:  {resp.data.get('grid_on')}")
                self.grid_on = resp.data.get("grid_on", False)
                self.last_act = resp.data.get("last_act", "None")
        msg = Message(
            content=f"RoundCount: {self.round_count}, action_state: {resp.action_state}",
            role=self.profile,
            cause_by=type(resp),
            send_from=self.name,
            send_to=self.name,
        )

        self.rc.memory.add(msg)
        return msg
