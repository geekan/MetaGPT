# -*- coding: utf-8 -*-
# @Desc    :

import pytest

from metagpt.actions.action_node import ActionNode
from metagpt.actions.prepare_interview import PrepareInterview


@pytest.mark.asyncio
async def test_action_serdeser(context):
    action = PrepareInterview(context=context)
    serialized_data = action.model_dump()
    assert serialized_data["name"] == "PrepareInterview"

    new_action = PrepareInterview(**serialized_data, context=context)

    assert new_action.name == "PrepareInterview"
    assert type(await new_action.run("python developer")) == ActionNode
