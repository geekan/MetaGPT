#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : qa_engineer.py
"""
import re
from pathlib import Path
from typing import Type

from metagpt.actions import WriteTest, WriteCode, WriteDesign, RunCode, DebugError
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.roles.engineer import Engineer
from metagpt.utils.common import CodeParser
from metagpt.utils.special_tokens import MSG_SEP, FILENAME_CODE_SEP

class QaEngineer(Role):
    def __init__(self, name="Edward", profile="QA Engineer",
                 goal="Write comprehensive and robust tests to ensure codes will work as expected without bugs",
                 constraints="The test code you write should conform to code standard like PEP8, be modular, easy to read and maintain"):
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteTest])
        self._watch([WriteCode])
    
    @classmethod
    def parse_workspace(cls, system_design_msg: Message) -> str:
        if not system_design_msg.instruct_content:
            return system_design_msg.instruct_content.dict().get("Python package name")
        return CodeParser.parse_str(block="Python package name", text=system_design_msg.content)
    
    def get_workspace(self, return_proj_dir=True) -> Path:
        msg = self._rc.memory.get_by_action(WriteDesign)[-1]
        if not msg:
            return WORKSPACE_ROOT / 'src'
        workspace = self.parse_workspace(msg)
        # project directory: workspace/{package_name}, which contains package source code folder, tests folder, resources folder, etc.
        # source codes directory: workspace/{package_name}/{package_name}
        if return_proj_dir:
            return WORKSPACE_ROOT / workspace
        return WORKSPACE_ROOT / workspace / workspace
        
    
    def write_file(self, filename: str, code: str):
        workspace = self.get_workspace() / 'tests'
        file = workspace / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(code)

    def recv(self, message: Message) -> None:
        self._rc.memory.add(message)

    async def _write_test(self, message: Message) -> None:

        code_msgs = message.content.split(MSG_SEP)
        result_msg_all = []
        for code_msg in code_msgs:

            # write tests
            file_name, file_path, code_to_test = code_msg.split(FILENAME_CODE_SEP)
            test_file_name = "test_" + file_name
            logger.info(f'Writing {test_file_name}..')
            test_code = await WriteTest().run(
                code_to_test=code_to_test,
                test_file_name=test_file_name,
                # source_file_name=file_name,
                source_file_path=file_path,
                workspace=self.get_workspace()
            )
            self.write_file(test_file_name, test_code)

            # run tests
            result_msg = await RunCode().run(
                mode="script",
                code=code_to_test,
                code_file_name=file_name,
                test_code=test_code,
                test_file_name=test_file_name,
                command=['python', f'tests/{test_file_name}'],
                working_directory=self.get_workspace(), # workspace/package_name, will run tests/test_xxx.py here
                additional_python_paths=[self.get_workspace(return_proj_dir=False)], # workspace/package_name/package_name,
                                                                                     # import statement inside package code needs this
            )

            result_msg_all.append(result_msg)

        # RunCode().run(
        #     mode="script",
        #     working_directory=self.get_workspace(),
        #     additional_python_paths=[self.get_workspace(return_proj_dir=False)],
        #     command=['python', '-m', 'unittest', 'discover', '-s', 'tests']
        # )
        logger.info(f'Done {self.get_workspace()}/tests generating.')
        msg_content = MSG_SEP.join(result_msg_all)
        msg = Message(content=msg_content, role=self.profile, cause_by=RunCode, send_to=QaEngineer)
        return msg
    
    async def _debug_error(self, msg):
        # process the msg, if the code works fine, no need to debug

        # else: debug and rewrite the code

        pass

    async def _act(self) -> Message:
        for msg in self._rc.news:
            if msg.send_to != "QaEngineer":
                continue
            if msg.cause_by == WriteCode:
                # engineer wrote a code, write a test for it
                result_msg = await self._write_test(msg)
            elif msg.cause_by == RunCode:
                # I wrote and ran my test code, fix bugs, if any
                result_msg = await self._debug_error(msg)
            
        return result_msg
