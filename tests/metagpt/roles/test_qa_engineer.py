#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 12:01
@Author  : alexanderwu
@File    : test_qa_engineer.py
"""
from pathlib import Path
from typing import List

import pytest
from pydantic import Field

from metagpt.actions import DebugError, RunCode, WriteTest
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.environment import Environment
from metagpt.roles import QaEngineer
from metagpt.schema import Message
from metagpt.utils.common import any_to_str, aread, awrite


async def test_qa(context):
    # Prerequisites
    demo_path = Path(__file__).parent / "../../data/demo_project"
    context.src_workspace = Path(context.repo.workdir) / "qa/game_2048"
    data = await aread(filename=demo_path / "game.py", encoding="utf-8")
    await awrite(filename=context.src_workspace / "game.py", data=data, encoding="utf-8")
    await awrite(filename=Path(context.repo.workdir) / "requirements.txt", data="")

    class MockEnv(Environment):
        msgs: List[Message] = Field(default_factory=list)

        def publish_message(self, message: Message, peekable: bool = True) -> bool:
            self.msgs.append(message)
            return True

    env = MockEnv()

    role = QaEngineer(context=context)
    role.set_env(env)
    await role.run(with_message=Message(content="", cause_by=SummarizeCode))
    assert env.msgs
    assert env.msgs[0].cause_by == any_to_str(WriteTest)
    msg = env.msgs[0]
    env.msgs.clear()
    await role.run(with_message=msg)
    assert env.msgs
    assert env.msgs[0].cause_by == any_to_str(RunCode)
    msg = env.msgs[0]
    env.msgs.clear()
    await role.run(with_message=msg)
    assert env.msgs
    assert env.msgs[0].cause_by == any_to_str(DebugError)
    msg = env.msgs[0]
    env.msgs.clear()
    role.test_round_allowed = 1
    rsp = await role.run(with_message=msg)
    assert "Exceeding" in rsp.content


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
