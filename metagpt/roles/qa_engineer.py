#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : qa_engineer.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.2.1 and 2.2.2 of RFC 116, modify the data
        type of the `cause_by` value in the `Message` to a string, and utilize the new message filtering feature.
"""
import json

from metagpt.actions import DebugError, RunCode, WriteCode, WriteCodeReview, WriteTest
from metagpt.config import CONFIG
from metagpt.const import OUTPUTS_FILE_REPO, TEST_CODES_FILE_REPO
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Document, Message, RunCodeContext, TestingContext
from metagpt.utils.common import CodeParser, any_to_str_set


class QaEngineer(Role):
    def __init__(
        self,
        name="Edward",
        profile="QaEngineer",
        goal="Write comprehensive and robust tests to ensure codes will work as expected without bugs",
        constraints="The test code you write should conform to code standard like PEP8, be modular, easy to read and maintain",
        test_round_allowed=5,
    ):
        super().__init__(name, profile, goal, constraints)
        self._init_actions(
            [WriteTest]
        )  # FIXME: a bit hack here, only init one action to circumvent _think() logic, will overwrite _think() in future updates
        self._watch([WriteCode, WriteCodeReview, WriteTest, RunCode, DebugError])
        self.test_round = 0
        self.test_round_allowed = test_round_allowed

    @classmethod
    def parse_workspace(cls, system_design_msg: Message) -> str:
        if system_design_msg.instruct_content:
            return system_design_msg.instruct_content.dict().get("Python package name")
        return CodeParser.parse_str(block="Python package name", text=system_design_msg.content)

    async def _write_test(self, message: Message) -> None:
        changed_files = message.content.splitlines()
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        tests_file_repo = CONFIG.git_repo.new_file_repository(TEST_CODES_FILE_REPO)
        for filename in changed_files:
            # write tests
            if not filename or "test" in filename:
                continue
            code_doc = await src_file_repo.get(filename)
            test_doc = await tests_file_repo.get("test_" + code_doc.filename)
            if not test_doc:
                test_doc = Document(
                    root_path=str(tests_file_repo.root_path), filename="test_" + code_doc.filename, content=""
                )
            logger.info(f"Writing {test_doc.filename}..")
            context = TestingContext(filename=test_doc.filename, test_doc=test_doc, code_doc=code_doc)
            context = await WriteTest(context=context, llm=self._llm).run()
            await tests_file_repo.save(
                filename=context.test_doc.filename,
                content=context.test_doc.content,
                dependencies={context.code_doc.root_relative_path},
            )

            # prepare context for run tests in next round
            run_code_context = RunCodeContext(
                command=["python", context.test_doc.root_relative_path],
                code_filename=context.code_doc.filename,
                test_filename=context.test_doc.filename,
                working_directory=str(CONFIG.git_repo.workdir),
                additional_python_paths=[CONFIG.src_workspace],
            )

            msg = Message(
                content=run_code_context.json(),
                role=self.profile,
                cause_by=WriteTest,
                sent_from=self,
                send_to=self,
            )
            self.publish_message(msg)

        logger.info(f"Done {str(tests_file_repo.workdir)} generating.")

    async def _run_code(self, msg):
        m = json.loads(msg.content)
        run_code_context = RunCodeContext(**m)
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        src_doc = await src_file_repo.get(run_code_context.code_filename)
        if not src_doc:
            return
        test_file_repo = CONFIG.git_repo.new_file_repository(TEST_CODES_FILE_REPO)
        test_doc = await test_file_repo.get(run_code_context.test_filename)
        if not test_doc:
            return
        run_code_context.code = src_doc.content
        run_code_context.test_code = test_doc.content
        result_msg = await RunCode(context=run_code_context, llm=self._llm).run()
        outputs_file_repo = CONFIG.git_repo.new_file_repository(OUTPUTS_FILE_REPO)
        run_code_context.output_filename = run_code_context.test_filename + ".log"
        await outputs_file_repo.save(
            filename=run_code_context.output_filename,
            content=result_msg,
            dependencies={src_doc.root_relative_path, test_doc.root_relative_path},
        )
        run_code_context.code = None
        run_code_context.test_code = None
        msg = Message(
            content=run_code_context.json(), role=self.profile, cause_by=RunCode, sent_from=self, send_to=self
        )
        self.publish_message(msg)

    async def _debug_error(self, msg):
        m = json.loads(msg.context)
        run_code_context = RunCodeContext(**m)
        output_file_repo = CONFIG.git_repo.new_file_repository(OUTPUTS_FILE_REPO)
        output_doc = await output_file_repo.get(run_code_context.output_filename)
        if not output_doc:
            return
        run_code_context.output = output_doc.content
        code = await DebugError(context=run_code_context, llm=self._llm).run()
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        await src_file_repo.save(filename=run_code_context.code_filename, content=code)
        run_code_context.output = None
        run_code_context.output_filename = None
        msg = Message(
            content=run_code_context.json(),
            role=self.profile,
            cause_by=DebugError,
            sent_from=self,
            send_to=self,
        )
        self.publish_message(msg)

    async def _act(self) -> Message:
        if self.test_round > self.test_round_allowed:
            result_msg = Message(
                content=f"Exceeding {self.test_round_allowed} rounds of tests, skip (writing code counts as a round, too)",
                role=self.profile,
                cause_by=WriteTest,
                sent_from=self.profile,
                send_to="",
            )
            return result_msg

        code_filters = any_to_str_set({WriteCode, WriteCodeReview})
        test_filters = any_to_str_set({WriteTest, DebugError})
        run_filters = any_to_str_set({RunCode})
        for msg in self._rc.news:
            # Decide what to do based on observed msg type, currently defined by human,
            # might potentially be moved to _think, that is, let the agent decides for itself
            if msg.cause_by in code_filters:
                # engineer wrote a code, time to write a test for it
                await self._write_test(msg)
            elif msg.cause_by in test_filters:
                # I wrote or debugged my test code, time to run it
                await self._run_code(msg)
            elif msg.cause_by in run_filters:
                # I ran my test code, time to fix bugs, if any
                await self._debug_error(msg)
        self.test_round += 1
        result_msg = Message(
            content=f"Round {self.test_round} of tests done",
            role=self.profile,
            cause_by=WriteTest,
            sent_from=self.profile,
            send_to="",
        )
        return result_msg
