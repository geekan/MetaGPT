#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of ahttp_client

import pytest

from metagpt.utils.ahttp_client import apost, apost_stream


@pytest.mark.asyncio
async def test_apost():
    result = await apost(url="https://www.baidu.com/")
    assert "百度一下" in result

    result = await apost(
        url="http://aider.meizu.com/app/weather/listWeather", data={"cityIds": "101240101"}, as_json=True
    )
    assert result["code"] == "200"


@pytest.mark.asyncio
async def test_apost_stream():
    result = apost_stream(url="https://www.baidu.com/")
    async for line in result:
        assert len(line) >= 0

    result = apost_stream(url="http://aider.meizu.com/app/weather/listWeather", data={"cityIds": "101240101"})
    async for line in result:
        assert len(line) >= 0
