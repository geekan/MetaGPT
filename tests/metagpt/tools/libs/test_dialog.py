#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from metagpt.actions.intent_detect import IntentDetectResult
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.tools.libs.dialog import intent_detect, software_development_intent_detect
from tests.metagpt.actions.test_intent_detect import DEMO_CONTENT


@pytest.mark.asyncio
@pytest.mark.skip
async def test_intent_detect():
    messages = [Message.model_validate(i) for i in DEMO_CONTENT]
    result = await intent_detect(messages)
    assert isinstance(result, IntentDetectResult)
    assert result
    logger.info(f"dialog:{DEMO_CONTENT}\nresult:{result.model_dump_json()}")


@pytest.mark.asyncio
async def test_software_develop_intent_detect():
    messages = [Message.model_validate(i) for i in DEMO_CONTENT]
    result = await software_development_intent_detect(messages)
    assert isinstance(result, IntentDetectResult)
    assert result
    logger.info(f"dialog:{DEMO_CONTENT}\nresult:{result.model_dump_json()}")


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
