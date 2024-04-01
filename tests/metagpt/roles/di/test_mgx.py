#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List

import pytest

from metagpt.context import Context
from metagpt.roles.di.mgx import MGX
from metagpt.schema import Message
from tests.metagpt.actions.test_intent_detect import (
    DEMO1_CONTENT,
    DEMO2_CONTENT,
    DEMO_CONTENT,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_messages",
    [
        [Message.model_validate(i) for i in DEMO2_CONTENT if i["role"] == "user"],
        [Message.model_validate(i) for i in DEMO_CONTENT if i["role"] == "user"],
        [Message.model_validate(i) for i in DEMO1_CONTENT if i["role"] == "user"],
    ],
)
# @pytest.mark.skip
async def test_mgx(user_messages: List[Message], context):
    ctx = context
    mgx = MGX(context=ctx, tools=["<all>"])

    for i, msg in enumerate(user_messages):
        await mgx.run(msg)
        data = mgx.model_dump_json()
        await context.repo.test_outputs.save(filename=f"{i}.json", content=data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_message", "history_messages"),
    [(Message.model_validate(DEMO2_CONTENT[2]), [Message.model_validate(i) for i in DEMO2_CONTENT[0:2]])],
)
# @pytest.mark.skip
async def test_mgx_fixbug(user_message: Message, history_messages: List[Message], context):
    ctx = Context()
    mgx = MGX(context=ctx, tools=["<all>"])
    mgx.rc.memory.add_batch(history_messages)
    await mgx.run(user_message)
    data = mgx.model_dump_json()
    await context.repo.test_outputs.save(filename="test_mgx_fixbug.json", content=data)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
