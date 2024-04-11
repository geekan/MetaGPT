#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import json
from http import HTTPStatus
from typing import Any, AsyncGenerator, Dict, List, Union

import dashscope
from dashscope.aigc.generation import Generation
from dashscope.api_entities.aiohttp_request import AioHttpRequest
from dashscope.api_entities.api_request_data import ApiRequestData
from dashscope.api_entities.api_request_factory import _get_protocol_params
from dashscope.api_entities.dashscope_response import (
    GenerationOutput,
    GenerationResponse,
    Message,
)
from dashscope.client.base_api import BaseAioApi
from dashscope.common.constants import SERVICE_API_PATH, ApiProtocol
from dashscope.common.error import (
    InputDataRequired,
    InputRequired,
    ModelRequired,
    UnsupportedApiProtocol,
)

from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM, LLMConfig
from metagpt.provider.llm_provider_registry import LLMType, register_provider
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.token_counter import DASHSCOPE_TOKEN_COSTS


def build_api_arequest(
    model: str, input: object, task_group: str, task: str, function: str, api_key: str, is_service=True, **kwargs
):
    (
        api_protocol,
        ws_stream_mode,
        is_binary_input,
        http_method,
        stream,
        async_request,
        query,
        headers,
        request_timeout,
        form,
        resources,
    ) = _get_protocol_params(kwargs)
    task_id = kwargs.pop("task_id", None)
    if api_protocol in [ApiProtocol.HTTP, ApiProtocol.HTTPS]:
        if not dashscope.base_http_api_url.endswith("/"):
            http_url = dashscope.base_http_api_url + "/"
        else:
            http_url = dashscope.base_http_api_url

        if is_service:
            http_url = http_url + SERVICE_API_PATH + "/"

        if task_group:
            http_url += "%s/" % task_group
        if task:
            http_url += "%s/" % task
        if function:
            http_url += function
        request = AioHttpRequest(
            url=http_url,
            api_key=api_key,
            http_method=http_method,
            stream=stream,
            async_request=async_request,
            query=query,
            timeout=request_timeout,
            task_id=task_id,
        )
    else:
        raise UnsupportedApiProtocol("Unsupported protocol: %s, support [http, https, websocket]" % api_protocol)

    if headers is not None:
        request.add_headers(headers=headers)

    if input is None and form is None:
        raise InputDataRequired("There is no input data and form data")

    request_data = ApiRequestData(
        model,
        task_group=task_group,
        task=task,
        function=function,
        input=input,
        form=form,
        is_binary_input=is_binary_input,
        api_protocol=api_protocol,
    )
    request_data.add_resources(resources)
    request_data.add_parameters(**kwargs)
    request.data = request_data
    return request


class AGeneration(Generation, BaseAioApi):
    @classmethod
    async def acall(
        cls,
        model: str,
        prompt: Any = None,
        history: list = None,
        api_key: str = None,
        messages: List[Message] = None,
        plugins: Union[str, Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[GenerationResponse, AsyncGenerator[GenerationResponse, None]]:
        if (prompt is None or not prompt) and (messages is None or not messages):
            raise InputRequired("prompt or messages is required!")
        if model is None or not model:
            raise ModelRequired("Model is required!")
        task_group, function = "aigc", "generation"  # fixed value
        if plugins is not None:
            headers = kwargs.pop("headers", {})
            if isinstance(plugins, str):
                headers["X-DashScope-Plugin"] = plugins
            else:
                headers["X-DashScope-Plugin"] = json.dumps(plugins)
            kwargs["headers"] = headers
        input, parameters = cls._build_input_parameters(model, prompt, history, messages, **kwargs)

        api_key, model = BaseAioApi._validate_params(api_key, model)
        request = build_api_arequest(
            model=model,
            input=input,
            task_group=task_group,
            task=Generation.task,
            function=function,
            api_key=api_key,
            **kwargs,
        )
        response = await request.aio_call()
        is_stream = kwargs.get("stream", False)
        if is_stream:

            async def aresp_iterator(response):
                async for resp in response:
                    yield GenerationResponse.from_api_response(resp)

            return aresp_iterator(response)
        else:
            return GenerationResponse.from_api_response(response)


@register_provider(LLMType.DASHSCOPE)
class DashScopeLLM(BaseLLM):
    def __init__(self, llm_config: LLMConfig):
        self.config = llm_config
        self.use_system_prompt = False  # only some models support system_prompt
        self.__init_dashscope()
        self.cost_manager = CostManager(token_costs=self.token_costs)

    def __init_dashscope(self):
        self.model = self.config.model
        self.api_key = self.config.api_key
        self.token_costs = DASHSCOPE_TOKEN_COSTS
        self.aclient: AGeneration = AGeneration

        # check support system_message models
        support_system_models = [
            "qwen-",  # all support
            "llama2-",  # all support
            "baichuan2-7b-chat-v1",
            "chatglm3-6b",
        ]
        for support_model in support_system_models:
            if support_model in self.model:
                self.use_system_prompt = True

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {
            "api_key": self.api_key,
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "result_format": "message",
        }
        if self.config.temperature > 0:
            # different model has default temperature. only set when it"s specified.
            kwargs["temperature"] = self.config.temperature
        if stream:
            kwargs["incremental_output"] = True
        return kwargs

    def _check_response(self, resp: GenerationResponse):
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(f"code: {resp.code}, request_id: {resp.request_id}, message: {resp.message}")

    def get_choice_text(self, output: GenerationOutput) -> str:
        return output.get("choices", [{}])[0].get("message", {}).get("content", "")

    def completion(self, messages: list[dict]) -> GenerationOutput:
        resp: GenerationResponse = self.aclient.call(**self._const_kwargs(messages, stream=False))
        self._check_response(resp)

        self._update_costs(dict(resp.usage))
        return resp.output

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> GenerationOutput:
        resp: GenerationResponse = await self.aclient.acall(**self._const_kwargs(messages, stream=False))
        self._check_response(resp)
        self._update_costs(dict(resp.usage))
        return resp.output

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> GenerationOutput:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        resp = await self.aclient.acall(**self._const_kwargs(messages, stream=True))
        collected_content = []
        usage = {}
        async for chunk in resp:
            self._check_response(chunk)
            content = chunk.output.choices[0]["message"]["content"]
            usage = dict(chunk.usage)  # each chunk has usage
            log_llm_stream(content)
            collected_content.append(content)
        log_llm_stream("\n")
        self._update_costs(usage)
        full_content = "".join(collected_content)
        return full_content
