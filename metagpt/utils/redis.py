# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author: Hui
# @Desc: { redis client }
# @Date: 2022/11/28 10:12
import json
import traceback
from datetime import timedelta
from enum import Enum
from typing import Awaitable, Callable, Dict, Optional, Union

from redis import asyncio as aioredis

from metagpt.config import CONFIG
from metagpt.logs import logger


class RedisTypeEnum(Enum):
    """Redis 数据类型"""

    String = "String"
    List = "List"
    Hash = "Hash"
    Set = "Set"
    ZSet = "ZSet"


def make_url(
    dialect: str,
    *,
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[Union[str, int]] = None,
    name: Optional[Union[str, int]] = None,
) -> str:
    url_parts = [f"{dialect}://"]
    if user or password:
        if user:
            url_parts.append(user)
        if password:
            url_parts.append(f":{password}")
        url_parts.append("@")

    if not host and not dialect.startswith("sqlite"):
        host = "127.0.0.1"

    if host:
        url_parts.append(f"{host}")
        if port:
            url_parts.append(f":{port}")

    # 比如redis可能传入0
    if name is not None:
        url_parts.append(f"/{name}")
    return "".join(url_parts)


class RedisAsyncClient(aioredis.Redis):
    """异步的客户端
    例子::

        rdb = RedisAsyncClient()
        print(rdb.url)

    Args:
        host: 服务器地址
        port: 服务器端口
        user: 用户名
        db:   数据库
        password: 密码
        decode_responses: 字符串输入被编码成utf8存储在Redis里了，而取出来的时候还是被编码后的bytes，需要显示的decode才能变成字符串
        health_check_interval: 定时检测连接，防止出现ConnectionErrors (104, Connection reset by peer)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = None,
        decode_responses=True,
        health_check_interval=10,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        socket_keepalive=True,
        **kwargs,
    ):
        super().__init__(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses,
            health_check_interval=health_check_interval,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            socket_keepalive=socket_keepalive,
            **kwargs,
        )
        self.url = make_url("redis", host=host, port=port, name=db, password=password)


class RedisCacheInfo(object):
    """统一缓存信息类"""

    def __init__(self, key, timeout: Union[int, timedelta] = timedelta(seconds=60), data_type=RedisTypeEnum.String):
        """
        缓存信息类初始化
        Args:
            key: 缓存的key
            timeout: 缓存过期时间, 单位秒
            data_type: 缓存采用的数据结构 (不传并不影响，用于标记业务采用的是什么数据结构)
        """
        self.key = key
        self.timeout = timeout
        self.data_type = data_type

    def __str__(self):
        return f"cache key {self.key} timeout {self.timeout}s"


class RedisManager:
    client: RedisAsyncClient = None

    @classmethod
    def init_redis_conn(cls, host, port, password, db):
        """初始化redis 连接"""
        if cls.client is None:
            cls.client = RedisAsyncClient(host=host, port=port, password=password, db=db)

    @classmethod
    async def set_with_cache_info(cls, redis_cache_info: RedisCacheInfo, value):
        """
        根据 RedisCacheInfo 设置 Redis 缓存
        :param redis_cache_info: RedisCacheInfo缓存信息对象
        :param value: 缓存的值
        :return:
        """
        await cls.client.setex(redis_cache_info.key, redis_cache_info.timeout, value)

    @classmethod
    async def get_with_cache_info(cls, redis_cache_info: RedisCacheInfo):
        """
        根据 RedisCacheInfo 获取 Redis 缓存
        :param redis_cache_info: RedisCacheInfo 缓存信息对象
        :return:
        """
        cache_info = await cls.client.get(redis_cache_info.key)
        return cache_info

    @classmethod
    async def del_with_cache_info(cls, redis_cache_info: RedisCacheInfo):
        """
        根据 RedisCacheInfo 删除 Redis 缓存
        :param redis_cache_info: RedisCacheInfo缓存信息对象
        :return:
        """
        await cls.client.delete(redis_cache_info.key)

    @staticmethod
    async def get_or_set_cache(cache_info: RedisCacheInfo, fetch_data_func: Callable[[], Awaitable[dict]]) -> dict:
        """
        获取缓存数据，如果缓存不存在，则从提供的函数中获取并设置缓存
        当前版本仅支持 json 形式的 string 格式数据
        """

        serialized_data = await RedisManager.get_with_cache_info(cache_info)

        if serialized_data:
            return json.loads(serialized_data)

        data = await fetch_data_func()
        try:
            serialized_data = json.dumps(data)
            await RedisManager.set_with_cache_info(cache_info, serialized_data)
        except Exception as e:
            logger.warning(f"数据 {data} 通过 json 进行序列化缓存失败:{e}")

        return data

    @classmethod
    def is_valid(cls):
        return cls.client is not None


class Redis:
    def __init__(self, conf: Dict = None):
        try:
            host = CONFIG.REDIS_HOST
            port = int(CONFIG.REDIS_PORT)
            pwd = CONFIG.REDIS_PASSWORD
            db = CONFIG.REDIS_DB
            RedisManager.init_redis_conn(host=host, port=port, password=pwd, db=db)
        except Exception as e:
            logger.warning(f"Redis initialization has failed:{e}")

    def is_valid(self):
        return RedisManager.is_valid()

    async def get(self, key: str) -> str:
        if not self.is_valid() or not key:
            return None
        try:
            v = await RedisManager.get_with_cache_info(redis_cache_info=RedisCacheInfo(key=key))
            return v
        except Exception as e:
            logger.exception(f"{e}, stack:{traceback.format_exc()}")
            return None

    async def set(self, key: str, data: str, timeout_sec: int):
        if not self.is_valid() or not key:
            return
        try:
            await RedisManager.set_with_cache_info(
                redis_cache_info=RedisCacheInfo(key=key, timeout=timeout_sec), value=data
            )
        except Exception as e:
            logger.exception(f"{e}, stack:{traceback.format_exc()}")
