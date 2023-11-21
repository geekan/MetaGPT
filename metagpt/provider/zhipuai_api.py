#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : zhipuai LLM from https://open.bigmodel.cn/dev/api#sdk

from enum import Enum
import json
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)
from requests import ConnectionError

import openai
import zhipuai

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.provider.openai_api import CostManager, log_and_reraise
from metagpt.provider.zhipuai.zhipu_model_api import ZhiPuModelAPI


class ZhiPuEvent(Enum):
    ADD = "add"
    ERROR = "error"
    INTERRUPTED = "interrupted"
    FINISH = "finish"


class ZhiPuAIGPTAPI(BaseGPTAPI):
    """
    Refs to `https://open.bigmodel.cn/dev/api#chatglm_turbo`
    From now, there is only one model named `chatglm_turbo`
    """

    use_system_prompt: bool = False  # zhipuai has no system prompt when use api

    def __init__(self):
        self.__init_zhipuai(CONFIG)
        self.llm = ZhiPuModelAPI
        self.model = "chatglm_turbo"  # so far only one model, just use it
        self._cost_manager = CostManager()

    def __init_zhipuai(self, config: CONFIG):
        assert config.zhipuai_api_key
        zhipuai.api_key = config.zhipuai_api_key
        openai.api_key = zhipuai.api_key  # due to use openai sdk, set the api_key but it will't be used.

    def _const_kwargs(self, messages: list[dict]) -> dict:
        kwargs = {
            "model": self.model,
            "prompt": messages,
            "temperature": 0.3
        }
        return kwargs

    def _update_costs(self, usage: dict):
        """ update each request's token cost """
        if CONFIG.calc_usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                self._cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
            except Exception as e:
                logger.error("zhipuai updats costs failed!", e)

    def get_choice_text(self, resp: dict) -> str:
        """ get the first text of choice from llm response """
        assist_msg = resp.get("data", {}).get("choices", [{"role": "error"}])[-1]
        assert assist_msg["role"] == "assistant"
        return assist_msg.get("content")

    def completion(self, messages: list[dict]) -> dict:
        resp = self.llm.invoke(**self._const_kwargs(messages))
        usage = resp.get("data").get("usage")
        self._update_costs(usage)
        return resp

    async def _achat_completion(self, messages: list[dict]) -> dict:
        resp = await self.llm.ainvoke(**self._const_kwargs(messages))
        usage = resp.get("data").get("usage")
        self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict]) -> dict:
        return await self._achat_completion(messages)

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        response = await self.llm.asse_invoke(**self._const_kwargs(messages))
        collected_content = []
        usage = {}
        async for event in response.async_events():
            if event.event == ZhiPuEvent.ADD.value:
                content = event.data
                collected_content.append(content)
                print(content, end="")
            elif event.event == ZhiPuEvent.ERROR.value or event.event == ZhiPuEvent.INTERRUPTED.value:
                content = event.data
                logger.error(f"event error: {content}", end="")
                collected_content.append([content])
            elif event.event == ZhiPuEvent.FINISH.value:
                """
                event.meta
                    {
                        "task_status":"SUCCESS",
                        "usage":{
                            "completion_tokens":351,
                            "prompt_tokens":595,
                            "total_tokens":946
                        },
                        "task_id":"xx",
                        "request_id":"xxx"
                    }
                """
                meta = json.loads(event.meta)
                usage = meta.get("usage")
            else:
                print(f"zhipuapi else event: {event.data}", end="")

        self._update_costs(usage)
        full_content = "".join(collected_content)
        return full_content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(ConnectionError),
        retry_error_callback=log_and_reraise
    )
    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """ response in async with stream or non-stream mode """
        if stream:
            return await self._achat_completion_stream(messages)
        resp = await self._achat_completion(messages)
        return self.get_choice_text(resp)
