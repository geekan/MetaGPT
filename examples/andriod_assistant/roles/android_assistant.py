#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : android assistant to learn from app operations and operate apps
import time
from typing import Optional
from pathlib import Path
from pydantic import Field
from datetime import datetime

from examples.andriod_assistant.actions.manual_record import ManualRecord
from examples.andriod_assistant.actions.parse_record import ParseRecord
from examples.andriod_assistant.actions.screenshot_parse import ScreenshotParse
from examples.andriod_assistant.actions.self_learn_and_reflect import SelfLearnAndReflect
from examples.andriod_assistant.utils.schema import RunState, AndroidActionOutput
from metagpt.actions.add_requirement import UserRequirement
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message


class AndroidAssistant(Role):
    name: str = "Nick"
    profile: str = "AndroidAssistant"
    goal: str = "operate the mobile phone's apps with self-learn"

    task_desc: str = ""
    round_count: int = 0
    last_act: str = ""
    task_dir: Optional[Path] = Field(default=None)
    docs_dir: Optional[Path] = Field(default=None)
    grid_on: bool = Field(default=False)

    def __init__(self, **data):
        super().__init__(**data)

        self._watch([UserRequirement, AndroidActionOutput])

        app_name = config.get_other("app_name", "demo")
        curr_path = Path(__file__).parent
        data_dir = curr_path.joinpath("..", "output")
        cur_datetime = datetime.fromtimestamp(int(time.time())).strftime("%Y-%m-%d_%H-%M-%S")

        """Firstly, we decide the state with user config, further, we can do it automatically, like if it's new app,
        run the learn first and then do the act stage or learn it during the action.
        """
        if config.get_other("stage") == "learn" and config.get_other("mode") == "manual":
            # choose ManualRecord and then run ParseRecord
            # Remember, only run each action only one time, no need to run n_round.
            self.set_actions([ManualRecord, ParseRecord])
            self.task_dir = data_dir.joinpath(app_name, f"manual_learn_{cur_datetime}")
            self.docs_dir = data_dir.joinpath(app_name, f"manual_docs")
        elif config.get_other("stage") == "learn" and config.get_other("mode") == "auto":
            # choose SelfLearnAndReflect to run
            self.set_actions([SelfLearnAndReflect])
            self.task_dir = data_dir.joinpath(app_name, f"auto_learn_{cur_datetime}")
            self.docs_dir = data_dir.joinpath(app_name, f"auto_docs")
        elif config.get_other("stage") == "act":
            # choose ScreenshotParse to run
            self.set_actions([ScreenshotParse])
            self.task_dir = data_dir.joinpath(app_name, f"act_{cur_datetime}")
            if config.get_other("mode") == "manual":
                self.docs_dir = data_dir.joinpath(app_name, f"manual_docs")
            else:
                self.docs_dir = data_dir.joinpath(app_name, f"auto_docs")
        self._check_dir()

        self._set_react_mode(RoleReactMode.BY_ORDER)

    def _check_dir(self):
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    async def react(self) -> Message:
        self.round_count += 1
        result = await super().react()
        print(f"react result {result}")
        return result

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        # TODO 这里修改 Send to 会有作用吗?
        send_to = ""
        if isinstance(todo, ManualRecord):
            resp = await todo.run(
                task_dir=self.task_dir,
                task_desc=self.task_desc,
                env=self.rc.env
            )
        elif isinstance(todo, ParseRecord):
            resp = await todo.run(
                app_name=config.get_other("app_name", "demo"),
                task_dir=self.task_dir,
                docs_dir=self.docs_dir,
                env=self.rc.env
            )
        elif isinstance(todo, SelfLearnAndReflect):
            resp = await todo.run(
                round_count=self.round_count,
                task_desc=self.task_desc,
                last_act=self.last_act,
                task_dir=self.task_dir,
                docs_dir=self.docs_dir,
                env=self.rc.env
            )
            if resp.action_state == RunState.SUCCESS:
                self.last_act = resp.data.get("last_act")
                send_to = self.name
        elif isinstance(todo, ScreenshotParse):
            resp = await todo.run(
                round_count=self.round_count,
                task_desc=self.task_desc,
                last_act=self.last_act,
                task_dir=self.task_dir,
                docs_dir=self.docs_dir,
                grid_on=self.grid_on,
                env=self.rc.env
            )
            if resp.action_state == RunState.SUCCESS:
                self.grid_on = resp.data.get("grid_on")
                send_to = self.name

        msg = Message(
            content=f"RoundCount: {self.round_count}",
            role=self.profile,
            cause_by=type(todo),
            send_from=self.name,
            send_to=self.name
        )
        self.publish_message(msg)
        self.rc.memory.add(msg)
        return msg
