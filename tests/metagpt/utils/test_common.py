#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 16:19
@Author  : alexanderwu
@File    : test_common.py
@Modified by: mashenquan, 2023/11/21. Add unit tests.
"""

import os
import platform
from typing import Any, Set

import pytest
from pydantic import BaseModel

from metagpt.actions import RunCode
from metagpt.const import get_metagpt_root
from metagpt.roles.tutorial_assistant import TutorialAssistant
from metagpt.schema import Message
from metagpt.utils.common import any_to_str, any_to_str_set, check_cmd_exists


class TestGetProjectRoot:
    def change_etc_dir(self):
        # current_directory = Path.cwd()
        abs_root = "/etc"
        os.chdir(abs_root)

    def test_get_project_root(self):
        project_root = get_metagpt_root()
        assert project_root.name == "MetaGPT"

    def test_get_root_exception(self):
        self.change_etc_dir()
        project_root = get_metagpt_root()
        assert project_root

    def test_any_to_str(self):
        class Input(BaseModel):
            x: Any
            want: str

        inputs = [
            Input(x=TutorialAssistant, want="metagpt.roles.tutorial_assistant.TutorialAssistant"),
            Input(x=TutorialAssistant(), want="metagpt.roles.tutorial_assistant.TutorialAssistant"),
            Input(x=RunCode, want="metagpt.actions.run_code.RunCode"),
            Input(x=RunCode(), want="metagpt.actions.run_code.RunCode"),
            Input(x=Message, want="metagpt.schema.Message"),
            Input(x=Message(content=""), want="metagpt.schema.Message"),
            Input(x="A", want="A"),
        ]
        for i in inputs:
            v = any_to_str(i.x)
            assert v == i.want

    def test_any_to_str_set(self):
        class Input(BaseModel):
            x: Any
            want: Set

        inputs = [
            Input(
                x=[TutorialAssistant, RunCode(), "a"],
                want={"metagpt.roles.tutorial_assistant.TutorialAssistant", "metagpt.actions.run_code.RunCode", "a"},
            ),
            Input(
                x={TutorialAssistant, "a"},
                want={"metagpt.roles.tutorial_assistant.TutorialAssistant", "a"},
            ),
            Input(
                x=(TutorialAssistant, RunCode(), "a"),
                want={"metagpt.roles.tutorial_assistant.TutorialAssistant", "metagpt.actions.run_code.RunCode", "a"},
            ),
        ]
        for i in inputs:
            v = any_to_str_set(i.x)
            assert v == i.want

    def test_check_cmd_exists(self):
        class Input(BaseModel):
            command: str
            platform: str

        inputs = [
            {"command": "cat", "platform": "linux"},
            {"command": "ls", "platform": "linux"},
            {"command": "mspaint", "platform": "windows"},
        ]
        plat = "windows" if platform.system().lower() == "windows" else "linux"
        for i in inputs:
            seed = Input(**i)
            result = check_cmd_exists(seed.command)
            if plat == seed.platform:
                assert result == 0
            else:
                assert result != 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
