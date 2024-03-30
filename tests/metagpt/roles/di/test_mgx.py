#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List

import pytest

from metagpt.context import Context
from metagpt.roles.di.mgx import MGX
from metagpt.schema import Message
from tests.metagpt.actions.test_intent_detect import DEMO1_CONTENT, DEMO_CONTENT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_messages",
    [
        [Message.model_validate(i) for i in DEMO_CONTENT if i["role"] == "user"],
        [Message.model_validate(i) for i in DEMO1_CONTENT if i["role"] == "user"],
    ],
)
async def test_mgx(user_messages: List[Message]):
    ctx = Context()
    mgx = MGX(context=ctx, tools=["<all>"])

    for i in user_messages:
        await mgx.run(i)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
