#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_redis.py
"""

import mock
import pytest

from metagpt.config import CONFIG
from metagpt.utils.redis import Redis


async def async_mock_from_url(*args, **kwargs):
    mock_client = mock.AsyncMock()
    mock_client.set.return_value = None
    mock_client.get.side_effect = [b"test", b""]
    return mock_client


@pytest.mark.asyncio
@mock.patch("aioredis.from_url", return_value=async_mock_from_url())
async def test_redis(mock_from_url):
    # Mock
    # mock_client = mock.AsyncMock()
    # mock_client.set.return_value=None
    # mock_client.get.side_effect = [b'test', b'']
    # mock_from_url.return_value = mock_client

    # Prerequisites
    CONFIG.REDIS_HOST = "MOCK_REDIS_HOST"
    CONFIG.REDIS_PORT = "MOCK_REDIS_PORT"
    CONFIG.REDIS_PASSWORD = "MOCK_REDIS_PASSWORD"
    CONFIG.REDIS_DB = 0

    conn = Redis()
    assert not conn.is_valid
    await conn.set("test", "test", timeout_sec=0)
    assert await conn.get("test") == b"test"
    await conn.close()

    # Mock session env
    old_options = CONFIG.options.copy()
    new_options = old_options.copy()
    new_options["REDIS_HOST"] = "YOUR_REDIS_HOST"
    CONFIG.set_context(new_options)
    try:
        conn = Redis()
        await conn.set("test", "test", timeout_sec=0)
        assert not await conn.get("test") == b"test"
        await conn.close()
    finally:
        CONFIG.set_context(old_options)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
