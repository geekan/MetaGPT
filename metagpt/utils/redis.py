# !/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : redis.py
"""

import traceback
from datetime import timedelta

import aioredis  # https://aioredis.readthedocs.io/en/latest/getting-started/

from metagpt.config import CONFIG
from metagpt.logs import logger


class Redis:
    def __init__(self):
        self._client = None

    async def _connect(self, force=False):
        if self._client and not force:
            return True
        if not CONFIG.REDIS_HOST or not CONFIG.REDIS_PORT or CONFIG.REDIS_DB is None or CONFIG.REDIS_PASSWORD is None:
            return False

        try:
            self._client = await aioredis.from_url(
                f"redis://{CONFIG.REDIS_HOST}:{CONFIG.REDIS_PORT}",
                username=CONFIG.REDIS_USER,
                password=CONFIG.REDIS_PASSWORD,
                db=CONFIG.REDIS_DB,
            )
            return True
        except Exception as e:
            logger.warning(f"Redis initialization has failed:{e}")
        return False

    async def get(self, key: str) -> bytes:
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

    @property
    def is_valid(self):
        return bool(self._client)
