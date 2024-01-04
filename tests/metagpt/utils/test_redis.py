#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_redis.py
"""

import pytest

from metagpt.config2 import Config
from metagpt.utils.redis import Redis


@pytest.mark.asyncio
async def test_redis():
    redis = Config.default().redis

    conn = Redis(redis)
    await conn.set("test", "test", timeout_sec=0)
    assert await conn.get("test") == b"test"
    await conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
