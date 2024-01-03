#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_redis.py
"""

import pytest

from metagpt.config import CONFIG
from metagpt.utils.redis import Redis


@pytest.mark.asyncio
async def test_redis():
    # Prerequisites
    assert CONFIG.REDIS_HOST and CONFIG.REDIS_HOST != "YOUR_REDIS_HOST"
    assert CONFIG.REDIS_PORT and CONFIG.REDIS_PORT != "YOUR_REDIS_PORT"
    # assert CONFIG.REDIS_USER
    assert CONFIG.REDIS_PASSWORD is not None and CONFIG.REDIS_PASSWORD != "YOUR_REDIS_PASSWORD"
    assert CONFIG.REDIS_DB is not None and CONFIG.REDIS_DB != "YOUR_REDIS_DB_INDEX, str, 0-based"

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
