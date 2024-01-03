#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import pytest

from metagpt.provider.zhipuai.async_sse_client import AsyncSSEClient


@pytest.mark.asyncio
async def test_async_sse_client():
    class Iterator(object):
        async def __aiter__(self):
            yield b"data: test_value"

    async_sse_client = AsyncSSEClient(event_source=Iterator())
    async for event in async_sse_client.async_events():
        assert event.data, "test_value"

    class InvalidIterator(object):
        async def __aiter__(self):
            yield b"invalid: test_value"

    async_sse_client = AsyncSSEClient(event_source=InvalidIterator())
    async for event in async_sse_client.async_events():
        assert not event
