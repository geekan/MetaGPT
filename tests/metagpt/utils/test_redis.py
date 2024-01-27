#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_redis.py
"""
from unittest.mock import AsyncMock

import pytest

from metagpt.utils.redis import Redis


@pytest.mark.asyncio
async def test_redis(mocker):
    async def async_mock_from_url(*args, **kwargs):
        mock_client = AsyncMock()
        mock_client.set.return_value = None
        mock_client.get.return_value = b"test"
        return mock_client

    mocker.patch("aioredis.from_url", return_value=async_mock_from_url())
    mock_config = mocker.Mock()
    mock_config.to_url.return_value = "http://mock.com"
    mock_config.username = "mockusername"
    mock_config.password = "mockpwd"
    mock_config.db = "0"

    conn = Redis(mock_config)
    await conn.set("test", "test", timeout_sec=0)
    assert await conn.get("test") == b"test"
    await conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
