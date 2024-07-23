# !/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : redis.py
"""
from __future__ import annotations

import traceback
from datetime import timedelta

import redis.asyncio as aioredis

from metagpt.configs.redis_config import RedisConfig
from metagpt.logs import logger


class Redis:
    def __init__(self, config: RedisConfig = None):
        self.config = config
        self._client = None

    async def _connect(self, force=False):
        if self._client and not force:
            return True

        try:
            self._client = await aioredis.from_url(
                self.config.to_url(),
                username=self.config.username,
                password=self.config.password,
                db=self.config.db,
            )
            return True
        except Exception as e:
            logger.warning(f"Redis initialization has failed:{e}")
        return False

    async def get(self, key: str) -> bytes | None:
        if not await self._connect() or not key:
            return None
        try:
            v = await self._client.get(key)
            return v
        except Exception as e:
            logger.exception(f"{e}, stack:{traceback.format_exc()}")
            return None

    async def set(self, key: str, data: str, timeout_sec: int = None):
        if not await self._connect() or not key:
            return
        try:
            ex = None if not timeout_sec else timedelta(seconds=timeout_sec)
            await self._client.set(key, data, ex=ex)
        except Exception as e:
            logger.exception(f"{e}, stack:{traceback.format_exc()}")

    async def close(self):
        if not self._client:
            return
        await self._client.close()
        self._client = None
