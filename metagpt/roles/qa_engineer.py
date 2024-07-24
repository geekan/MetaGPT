#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : qa_engineer.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.2.1 and 2.2.2 of RFC 116, modify the data
        type of the `cause_by` value in the `Message` to a string, and utilize the new message filtering feature.
@Modified By: mashenquan, 2023-11-27.
        1. Following the think-act principle, solidify the task parameters when creating the
        WriteTest/RunCode/DebugError object, rather than passing them in when calling the run function.
        2. According to Section 2.2.3.5.7 of RFC 135, change the method of transferring files from using the Message
        to using file references.
@Modified By: mashenquan, 2023-12-5. Enhance the workflow to navigate to WriteCode or QaEngineer based on the results
    of SummarizeCode.
"""


from metagpt.actions import DebugError, RunCode, WriteTest
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.const import MESSAGE_ROUTE_TO_NONE
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Document, Message, RunCodeContext, TestingContext
from metagpt.utils.common import any_to_str_set, parse_recipient


class QaEngineer(Role):
    name: str = "Edward"
    profile: str = "QaEngineer"
    goal: str = "Write comprehensive and robust tests to ensure codes will work as expected without bugs"
    constraints: str = (
        "The test code you write should conform to code standard like PEP8, be modular, easy to read and maintain."
        "Use same language as user requirement"
    )
    test_round_allowed: int = 5
    test_round: int = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # FIXME: a bit hack here, only init one action to circumvent _think() logic,
        #  will overwrite _think() in future updates
        self.set_actions([WriteTest])
        self._watch([SummarizeCode, WriteTest, RunCode, DebugError])
        self.test_round = 0

    async def _write_test(self, message: Message) -> None:
        src_file_repo = self.project_repo.with_src_path(self.context.src_workspace).srcs
        changed_files = set(src_file_repo.changed_files.keys())
        # Unit tests only.
        if self.config.reqa_file and self.config.reqa_file not in changed_files:
            changed_files.add(self.config.reqa_file)
        for filename in changed_files:
            # write tests
            if not filename or "test" in filename:
                continue
            code_doc = await src_file_repo.get(filename)
            if not code_doc:
                continue
            if not code_doc.filename.endswith(".py"):
                continue
            test_doc = await self.project_repo.tests.get("test_" + code_doc.filename)
            if not test_doc:
                test_doc = Document(
                    root_path=str(self.project_repo.tests.root_path), filename="test_" + code_doc.filename, content=""
                )
            logger.info(f"Writing {test_doc.filename}..")
            context = TestingContext(filename=test_doc.filename, test_doc=test_doc, code_doc=code_doc)
            context = await WriteTest(i_context=context, context=self.context, llm=self.llm).run()
            await self.project_repo.tests.save_doc(
                doc=context.test_doc, dependencies={context.code_doc.root_relative_path}
            )

            # prepare context for run tests in next round
            run_code_context = RunCodeContext(
                command=["python", context.test_doc.root_relative_path],
                code_filename=context.code_doc.filename,
                test_filename=context.test_doc.filename,
                working_directory=str(self.project_repo.workdir),
                additional_python_paths=[str(self.context.src_workspace)],
            )
            self.publish_message(
                Message(
                    content=run_code_context.model_dump_json(),
                    role=self.profile,
                    cause_by=WriteTest,
                    sent_from=self,
                    send_to=self,
                )
            )

        logger.info(f"Done {str(self.project_repo.tests.workdir)} generating.")

    async def _run_code(self, msg):
        run_code_context = RunCodeContext.loads(msg.content)
        src_doc = await self.project_repo.with_src_path(self.context.src_workspace).srcs.get(
            run_code_context.code_filename
        )
        if not src_doc:
            return
        test_doc = await self.project_repo.tests.get(run_code_context.test_filename)
        if not test_doc:
            return
        run_code_context.code = src_doc.content
        run_code_context.test_code = test_doc.content
        result = await RunCode(i_context=run_code_context, context=self.context, llm=self.llm).run()
        run_code_context.output_filename = run_code_context.test_filename + ".json"
        await self.project_repo.test_outputs.save(
            filename=run_code_context.output_filename,
            content=result.model_dump_json(),
            dependencies={src_doc.root_relative_path, test_doc.root_relative_path},
        )
        run_code_context.code = None
        run_code_context.test_code = None
        # the recipient might be Engineer or myself
        recipient = parse_recipient(result.summary)
        mappings = {"Engineer": "Alex", "QaEngineer": "Edward"}
        self.publish_message(
            Message(
                content=run_code_context.model_dump_json(),
                role=self.profile,
                cause_by=RunCode,
                sent_from=self,
                send_to=mappings.get(recipient, MESSAGE_ROUTE_TO_NONE),
            )
        )

    async def _debug_error(self, msg):
        run_code_context = RunCodeContext.loads(msg.content)
        code = await DebugError(i_context=run_code_context, context=self.context, llm=self.llm).run()
        await self.project_repo.tests.save(filename=run_code_context.test_filename, content=code)
        run_code_context.output = None
        self.publish_message(
            Message(
                content=run_code_context.model_dump_json(),
                role=self.profile,
                cause_by=DebugError,
                sent_from=self,
                send_to=self,
            )
        )

    async def _act(self) -> Message:
        if self.test_round > self.test_round_allowed:
            result_msg = Message(
                content=f"Exceeding {self.test_round_allowed} rounds of tests, skip (writing code counts as a round, too)",
                role=self.profile,
                cause_by=WriteTest,
                sent_from=self.profile,
                send_to=MESSAGE_ROUTE_TO_NONE,
            )
            return result_msg

        code_filters = any_to_str_set({SummarizeCode})
        test_filters = any_to_str_set({WriteTest, DebugError})
        run_filters = any_to_str_set({RunCode})
        for msg in self.rc.news:
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
        return Message(
            content=f"Round {self.test_round} of tests done",
            role=self.profile,
            cause_by=WriteTest,
            sent_from=self.profile,
            send_to=MESSAGE_ROUTE_TO_NONE,
        )

    async def _observe(self, ignore_memory=False) -> int:
        # This role has events that trigger and execute themselves based on conditions, and cannot rely on the
        # content of memory to activate.
        return await super()._observe(ignore_memory=True)
