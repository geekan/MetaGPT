#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : android assistant to learn from app operations and operate apps

from examples.andriod_assistant.actions.manual_record import ManualRecord
from examples.andriod_assistant.actions.parse_record import ParseRecord
from examples.andriod_assistant.actions.screenshot_parse import ScreenshotParse
from examples.andriod_assistant.actions.self_learn import SelfLearn
from examples.andriod_assistant.actions.self_learn_reflect import SelfLearnReflect
from metagpt.actions.add_requirement import UserRequirement
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.roles.role import Role
from metagpt.schema import Message


class AndroidAssistant(Role):
    name: str = "Nick"
    profile: str = "AndroidAssistant"
    goal: str = "operate the phone apps with self-learn"

    def __init__(self, **data):
        super().__init__(**data)

        self._watch([UserRequirement])
        self.set_actions([ManualRecord, ParseRecord, SelfLearn, SelfLearnReflect, ScreenshotParse])

    async def _think(self) -> bool:
        """Firstly, we decide the state with user config, further, we can do it automatically, like if it's new app,
        run the learn first and then do the act stage or learn it during the action.
        """
        if config.get_other("stage") == "learn" and config.get_other("mode") == "manual":
            # choose ManualRecord and then run ParseRecord
            # Remember, only run each action only one time, no need to run n_round.
            pass
        elif config.get_other("stage") == "learn" and config.get_other("mode") == "auto":
            # choose SelfLearn / SelfLearnReflect to run
            pass
        elif config.get_other("stage") == "act":
            # choose ScreenshotParse to run
            pass

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
