# -*- coding: utf-8 -*-
# @Desc    :

import pytest

from metagpt.actions.action_node import ActionNode
from metagpt.actions.prepare_interview import PrepareInterview


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_action_deserialize():
    action = PrepareInterview()
    serialized_data = action.model_dump()
    assert serialized_data["name"] == "PrepareInterview"

    new_action = PrepareInterview(**serialized_data)

    assert new_action.name == "PrepareInterview"
    assert type(await new_action.run("python developer")) == ActionNode
