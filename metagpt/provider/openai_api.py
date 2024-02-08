# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
@Modified By: mashenquan, 2023/11/21. Fix bug: ReadTimeout.
@Modified By: mashenquan, 2023/12/1. Fix bug: Unclosed connection caused by openai 0.x.
"""

import json
import re
from typing import AsyncIterator, Optional, Union

from openai import APIConnectionError, AsyncOpenAI, AsyncStream
from openai._base_client import AsyncHttpxClientWrapper
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.constant import GENERAL_FUNCTION_SCHEMA
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.schema import Message
from metagpt.utils.common import CodeParser, decode_image
from metagpt.utils.cost_manager import CostManager, Costs
from metagpt.utils.exceptions import handle_exception
from metagpt.utils.token_counter import (
    count_message_tokens,
    count_string_tokens,
    get_max_completion_tokens,
)


def log_and_reraise(retry_state):
    logger.error(f"Retry attempts exhausted. Last exception: {retry_state.outcome.exception()}")
    logger.warning(
        """
Recommend going to https://deepwisdom.feishu.cn/wiki/MsGnwQBjiif9c3koSJNcYaoSnu4#part-XdatdVlhEojeAfxaaEZcMV3ZniQ
See FAQ 5.8
"""
    )
    raise retry_state.outcome.exception()


@register_provider(LLMType.OPENAI)
class OpenAILLM(BaseLLM):
    """Check https://platform.openai.com/examples for examples"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._init_model()
        self._init_client()
        self.auto_max_tokens = False
        self.cost_manager: Optional[CostManager] = None

    def _init_model(self):
        self.model = self.config.model  # Used in _calc_usage & _cons_kwargs

    def _init_client(self):
        """https://github.com/openai/openai-python#async-usage"""
        kwargs = self._make_client_kwargs()
        self.aclient = AsyncOpenAI(**kwargs)

    def _make_client_kwargs(self) -> dict:
        kwargs = {"api_key": self.config.api_key, "base_url": self.config.base_url}

        # to use proxy, openai v1 needs http_client
        if proxy_params := self._get_proxy_params():
            kwargs["http_client"] = AsyncHttpxClientWrapper(**proxy_params)

        return kwargs

    def _get_proxy_params(self) -> dict:
        params = {}
        if self.config.proxy:
            params = {"proxies": self.config.proxy}
            if self.config.base_url:
                params["base_url"] = self.config.base_url

        return params

    async def _achat_completion_stream(self, messages: list[dict], timeout=3) -> AsyncIterator[str]:
        response: AsyncStream[ChatCompletionChunk] = await self.aclient.chat.completions.create(
            **self._cons_kwargs(messages, timeout=timeout), stream=True
        )

        async for chunk in response:
            chunk_message = chunk.choices[0].delta.content or "" if chunk.choices else ""  # extract the message
            yield chunk_message

    def _cons_kwargs(self, messages: list[dict], timeout=3, **extra_kwargs) -> dict:
        kwargs = {
            "messages": messages,
            "max_tokens": self._get_max_tokens(messages),
            "n": 1,
            # "stop": None,  # default it's None and gpt4-v can't have this one
            "temperature": 0.3,
            "model": self.model,
            "timeout": max(self.config.timeout, timeout),
        }
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        return kwargs

    async def _achat_completion(self, messages: list[dict], timeout=3) -> ChatCompletion:
        kwargs = self._cons_kwargs(messages, timeout=timeout)
        rsp: ChatCompletion = await self.aclient.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage)
        return rsp

    async def acompletion(self, messages: list[dict], timeout=3) -> ChatCompletion:
        return await self._achat_completion(messages, timeout=timeout)

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(APIConnectionError),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        """when streaming, print each token in place."""
        if stream:
            resp = self._achat_completion_stream(messages, timeout=timeout)

            collected_messages = []
            async for i in resp:
                log_llm_stream(i)
                collected_messages.append(i)
            log_llm_stream("\n")

            full_reply_content = "".join(collected_messages)
            usage = self._calc_usage(messages, full_reply_content)
            self._update_costs(usage)
            return full_reply_content

        rsp = await self._achat_completion(messages, timeout=timeout)
        return self.get_choice_text(rsp)

    def _func_configs(self, messages: list[dict], timeout=3, **kwargs) -> dict:
        """Note: Keep kwargs consistent with https://platform.openai.com/docs/api-reference/chat/create"""
        if "tools" not in kwargs:
            configs = {"tools": [{"type": "function", "function": GENERAL_FUNCTION_SCHEMA}]}
            kwargs.update(configs)

        return self._cons_kwargs(messages=messages, timeout=timeout, **kwargs)

    def _process_message(self, messages: Union[str, Message, list[dict], list[Message], list[str]]) -> list[dict]:
        """convert messages to list[dict]."""
        # 全部转成list
        if not isinstance(messages, list):
            messages = [messages]

        # 转成list[dict]
        processed_messages = []
        for msg in messages:
            if isinstance(msg, str):
                processed_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict):
                assert set(msg.keys()) == set(["role", "content"])
                processed_messages.append(msg)
            elif isinstance(msg, Message):
                processed_messages.append(msg.to_dict())
            else:
                raise ValueError(
                    f"Only support message type are: str, Message, dict, but got {type(messages).__name__}!"
                )
        return processed_messages

    async def _achat_completion_function(self, messages: list[dict], timeout=3, **chat_configs) -> ChatCompletion:
        messages = self._process_message(messages)
        kwargs = self._func_configs(messages=messages, timeout=timeout, **chat_configs)
        rsp: ChatCompletion = await self.aclient.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage)
        return rsp

    async def aask_code(self, messages: list[dict], **kwargs) -> dict:
        """Use function of tools to ask a code.
        Note: Keep kwargs consistent with https://platform.openai.com/docs/api-reference/chat/create

        Examples:
        >>> llm = OpenAILLM()
        >>> msg = [{'role': 'user', 'content': "Write a python hello world code."}]
        >>> rsp = await llm.aask_code(msg)
        # -> {'language': 'python', 'code': "print('Hello, World!')"}
        """
        rsp = await self._achat_completion_function(messages, **kwargs)
        return self.get_choice_function_arguments(rsp)

    def _parse_arguments(self, arguments: str) -> dict:
        """parse arguments in openai function call"""
        if "langugae" not in arguments and "code" not in arguments:
            logger.warning(f"Not found `code`, `language`, We assume it is pure code:\n {arguments}\n. ")
            return {"language": "python", "code": arguments}

        # 匹配language
        language_pattern = re.compile(r'[\"\']?language[\"\']?\s*:\s*["\']([^"\']+?)["\']', re.DOTALL)
        language_match = language_pattern.search(arguments)
        language_value = language_match.group(1) if language_match else "python"

        # 匹配code
        code_pattern = r'(["\'`]{3}|["\'`])([\s\S]*?)\1'
        try:
            code_value = re.findall(code_pattern, arguments)[-1][-1]
        except Exception as e:
            logger.error(f"{e}, when re.findall({code_pattern}, {arguments})")
            code_value = None

        if code_value is None:
            raise ValueError(f"Parse code error for {arguments}")
        # arguments只有code的情况
        return {"language": language_value, "code": code_value}

    # @handle_exception
    def get_choice_function_arguments(self, rsp: ChatCompletion) -> dict:
        """Required to provide the first function arguments of choice.

        :param dict rsp: same as in self.get_choice_function(rsp)
        :return dict: return the first function arguments of choice, for example,
            {'language': 'python', 'code': "print('Hello, World!')"}
        """
        message = rsp.choices[0].message
        if (
            message.tool_calls is not None
            and message.tool_calls[0].function is not None
            and message.tool_calls[0].function.arguments is not None
        ):
            # reponse is code
            try:
                return json.loads(message.tool_calls[0].function.arguments, strict=False)
            except json.decoder.JSONDecodeError as e:
                error_msg = (
                    f"Got JSONDecodeError for \n{'--'*40} \n{message.tool_calls[0].function.arguments}, {str(e)}"
                )
                logger.error(error_msg)
                return self._parse_arguments(message.tool_calls[0].function.arguments)
        elif message.tool_calls is None and message.content is not None:
            # reponse is code, fix openai tools_call respond bug,
            # The response content is `code``, but it appears in the content instead of the arguments.
            code_formats = "```"
            if message.content.startswith(code_formats) and message.content.endswith(code_formats):
                code = CodeParser.parse_code(None, message.content)
                return {"language": "python", "code": code}
            # reponse is message
            return {"language": "markdown", "code": self.get_choice_text(rsp)}
        else:
            logger.error(f"Failed to parse \n {rsp}\n")
            raise Exception(f"Failed to parse \n {rsp}\n")

    def get_choice_text(self, rsp: ChatCompletion) -> str:
        """Required to provide the first text of choice"""
        return rsp.choices[0].message.content if rsp.choices else ""

    def _calc_usage(self, messages: list[dict], rsp: str) -> CompletionUsage:
        usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        if not self.config.calc_usage:
            return usage

        try:
            usage.prompt_tokens = count_message_tokens(messages, self.model)
            usage.completion_tokens = count_string_tokens(rsp, self.model)
        except Exception as e:
            logger.warning(f"usage calculation failed: {e}")

        return usage

    @handle_exception
    def _update_costs(self, usage: CompletionUsage):
        if self.config.calc_usage and usage and self.cost_manager:
            self.cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, self.model)

    def get_costs(self) -> Costs:
        if not self.cost_manager:
            return Costs(0, 0, 0, 0)
        return self.cost_manager.get_costs()

    def _get_max_tokens(self, messages: list[dict]):
        if not self.auto_max_tokens:
            return self.config.max_token
        # FIXME
        # https://community.openai.com/t/why-is-gpt-3-5-turbo-1106-max-tokens-limited-to-4096/494973/3
        return min(get_max_completion_tokens(messages, self.model, self.config.max_token), 4096)

    @handle_exception
    async def amoderation(self, content: Union[str, list[str]]):
        """Moderate content."""
        return await self.aclient.moderations.create(input=content)

    async def atext_to_speech(self, **kwargs):
        """text to speech"""
        return await self.aclient.audio.speech.create(**kwargs)

    async def aspeech_to_text(self, **kwargs):
        """speech to text"""
        return await self.aclient.audio.transcriptions.create(**kwargs)

    async def gen_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        model: str = None,
        resp_format: str = "url",
    ) -> list["Image"]:
        """image generate"""
        assert resp_format in ["url", "b64_json"]
        if not model:
            model = self.model
        res = await self.aclient.images.generate(
            model=model, prompt=prompt, size=size, quality=quality, n=1, response_format=resp_format
        )
        imgs = []
        for item in res.data:
            img_url_or_b64 = item.url if resp_format == "url" else item.b64_json
            imgs.append(decode_image(img_url_or_b64))
        return imgs
