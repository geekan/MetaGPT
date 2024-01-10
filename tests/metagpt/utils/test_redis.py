#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_redis.py
"""

import mock
import pytest

from metagpt.config2 import Config
from metagpt.utils.redis import Redis


async def async_mock_from_url(*args, **kwargs):
    mock_client = mock.AsyncMock()
    mock_client.set.return_value = None
    mock_client.get.side_effect = [b"test", b""]
    return mock_client


@pytest.mark.asyncio
@mock.patch("aioredis.from_url", return_value=async_mock_from_url())
async def test_redis(i):
    redis = Config.default().redis

    conn = Redis(redis)
    await conn.set("test", "test", timeout_sec=0)
    assert await conn.get("test") == b"test"
    await conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
