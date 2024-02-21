# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2023/12/27
# @Author  : mashenquan
# @File    : redis.py

from __future__ import annotations

import traceback
from datetime import timedelta

import aioredis  # https://aioredis.readthedocs.io/en/latest/getting-started/

from metagpt.configs.redis_config import RedisConfig
from metagpt.logs import logger


class Redis:
    """A class for managing Redis operations.

    This class provides asynchronous methods to connect to Redis, get and set values, and close the connection.

    Attributes:
        config (RedisConfig): Configuration for the Redis connection.
        _client: The Redis client instance.
    """

    def __init__(self, config: RedisConfig = None):
        """Initializes the Redis manager with optional configuration.

        Args:
            config: The configuration for the Redis connection.
        """
        self.config = config
        self._client = None

    async def _connect(self, force=False):
        """Establishes a connection to Redis.

        This method attempts to connect to Redis using the provided configuration. It supports
        forcefully re-establishing the connection.

        Args:
            force: A boolean flag to force reconnection even if a client already exists.

        Returns:
            True if the connection was successful, False otherwise.
        """
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
        """Retrieves a value from Redis by key.

        Args:
            key: The key for the value to retrieve.

        Returns:
            The value associated with the key if found, None otherwise.
        """
        if not await self._connect() or not key:
            return None
        try:
            v = await self._client.get(key)
            return v
        except Exception as e:
            logger.exception(f"{e}, stack:{traceback.format_exc()}")
            return None

    async def set(self, key: str, data: str, timeout_sec: int = None):
        """Sets a value in Redis with an optional timeout.

        Args:
            key: The key under which to store the value.
            data: The value to store.
            timeout_sec: The expiration timeout in seconds, if any.
        """
        if not await self._connect() or not key:
            return
        try:
            ex = None if not timeout_sec else timedelta(seconds=timeout_sec)
            await self._client.set(key, data, ex=ex)
        except Exception as e:
            logger.exception(f"{e}, stack:{traceback.format_exc()}")

    async def close(self):
        """Closes the Redis connection."""
        if not self._client:
            return
        await self._client.close()
        self._client = None
