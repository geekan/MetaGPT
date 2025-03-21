import time
import asyncio
import math
import json

from pydantic_core import to_jsonable_python
from metagpt.utils.token_counter import count_message_tokens
from metagpt.configs.llm_config import LLMConfig
from metagpt.logs import logger
from metagpt.configs.models_config import ModelsConfig
import metagpt.utils.common as common

class RateLimitor:
    def __init__(self, rpm: int, tpm: int):
        self.rpm = rpm
        self.tpm = tpm
        self.tpm_bucket = TokenBucket(tpm)
        self.rpm_bucket = TokenBucket(rpm)
        self.lock = asyncio.Semaphore(rpm)
    
    async def acquire_rpm(self, tokens=1):
        await self.rpm_bucket.acquire(tokens)

    
    async def __enter__(self):
        if self.rpm > 0 or self.tpm > 0:
            await self.lock.acquire()
        return self

    async def __exit__(self, exc_type, exc_val, exc_tb):
        if self.rpm > 0 or self.tpm > 0:
            self.lock.release()
        return None

    async def __aenter__(self):
        return await self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.__exit__(exc_type, exc_val, exc_tb)

    def cost_token(self, usage: dict):
        if not isinstance(usage, dict):
            usage = dict(usage)
        self.tpm_bucket._cost(usage.get("input_tokens", usage.get('prompt_tokens', 0)))
        self.tpm_bucket._cost(usage.get("output_tokens", usage.get('completion_tokens', 0)))
        

    async def acquire(self, messages):
        tokens = count_message_tokens(messages)
        await self.tpm_bucket._wait(tokens)
        await self.acquire_rpm(1)


class TokenBucket:
    def __init__(self, rpm):
        """
        Initialize the token bucket (thread-safe version)
        :param rpm: the number of requests per minute
        """
        if rpm is None:
            rpm = 0
        self.capacity = rpm        # the capacity of the bucket
        self.tokens = rpm          # the current number of tokens
        self.rate = rpm / 60.0 if rpm else 0  # the number of tokens generated per second
        self.last_refill = time.time()
        self.lock = asyncio.Lock()  # 线程安全锁

    async def _refill(self, desc_tokens=0):
        async with self.lock:
            """Refill the tokens (need to be called in the lock protected context)"""
            if self.capacity is None or self.capacity <= 0:
                return
            # assert self.capacity >= desc_tokens, f"令牌桶的容量[{self.capacity}]无法支撑该次请求的消耗:{desc_tokens}."
            now = time.time()
            elapsed = now - self.last_refill
            new_tokens = elapsed * self.rate
            
            if new_tokens + self.tokens >= desc_tokens or self.tokens >= self.capacity:
                self.tokens = min(self.capacity, self.tokens + new_tokens) - desc_tokens
                self.last_refill = now
                return True  # 表示有新增令牌
            else:
                self.tokens = min(self.capacity, self.tokens + new_tokens)
                self.last_refill = now
                return False
    
    def _cost(self, tokens: int):
        if self.capacity is None or self.capacity <= 0:
            return
        assert tokens >= 0
        common.asyncio_run(self._refill())
        self.tokens -= tokens

    async def _wait(self, tokens: int):
        while True:
            if await self._refill(desc_tokens=tokens):
                # enough tokens, return immediately
                return True
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate

            logger.warning(f"current [{asyncio.current_task().get_name()}] with [{self.tokens:.5f}] tokens, wait_time for tpm: {wait_time:.3f}")
            await asyncio.sleep(wait_time)

    async def acquire(self, tokens=1):
        """
        Block until acquiring the specified number of tokens
        :param tokens: the number of tokens needed (default is 1)
        """
        if self.capacity is None or self.capacity <= 0:
            return
        
        while True:
            # if the tokens are enough, return immediately
            if await self._refill(desc_tokens=tokens):
                return
            
            # calculate the time to wait
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate

            logger.warning(f"current [{asyncio.current_task().get_name()}] with [{self.tokens:.5f}] tokens, wait_time for rpm: {wait_time:.3f}")
            
            # wait until the tokens are replenished (with timeout and notification)
            await asyncio.sleep(wait_time)

    @property
    def available_tokens(self):
        """Get the current number of available tokens (refreshed in real time)"""
        if self.capacity is None or self.capacity <= 0:
            return math.inf
        common.asyncio_run(self._refill())
        return self.tokens
        

class RateLimitorRegistry:
    def __init__(self):
        self.rate_limitors = {}
        self.config_items = {}

    def init_rate_limitors(self):
        for model_name, llm_config in ModelsConfig.default().items():
            self.register(model_name, llm_config)

    def _config_to_key(self, llm_config: LLMConfig):
        return json.dumps(llm_config.model_dump(), default=to_jsonable_python)

    def register(self, model_name: str, llm_config: LLMConfig) -> RateLimitor:
        if not llm_config:
            raise ValueError("llm_config is required")
        if not model_name:
            model_name = self._config_to_key(llm_config)
        if model_name not in self.rate_limitors:
            self.rate_limitors[model_name] = RateLimitor(llm_config.rpm, llm_config.tpm)
            self.config_items[self._config_to_key(llm_config)] = model_name
        return self.rate_limitors[model_name]
    
    def get(self, model_name: str):
        if not model_name:
            model_name = "_default_llm"
        return self.rate_limitors.get(model_name)
    
    def get_by_config(self, llm_config: LLMConfig):
        rate_limitor_key = self._config_to_key(llm_config)
        return self.rate_limitors.get(rate_limitor_key, default_rate_limitor)

rate_limitor_registry = RateLimitorRegistry()

default_rate_limitor =  RateLimitor(0, 0)