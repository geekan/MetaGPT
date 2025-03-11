#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:04
@Author  : alexanderwu
@File    : base_llm.py
@Desc    : mashenquan, 2023/8/22. + try catch
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Optional, Union

from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from metagpt.configs.compress_msg_config import CompressType
from metagpt.configs.llm_config import LLMConfig
from metagpt.const import IMAGES, LLM_API_TIMEOUT, USE_CONFIG_TIMEOUT
from metagpt.logs import logger
from metagpt.provider.constant import MULTI_MODAL_MODELS
from metagpt.utils.common import log_and_reraise
from metagpt.utils.cost_manager import CostManager, Costs
from metagpt.utils.token_counter import TOKEN_MAX


class BaseLLM(ABC):
    """LLM API abstract class, requiring all inheritors to provide a series of standard capabilities"""

    config: LLMConfig
    use_system_prompt: bool = True
    system_prompt = "You are a helpful assistant."

    # OpenAI / Azure / Others
    aclient: Optional[Union[AsyncOpenAI]] = None
    cost_manager: Optional[CostManager] = None
    model: Optional[str] = None  # deprecated
    pricing_plan: Optional[str] = None

    _reasoning_content: Optional[str] = None  # content from reasoning mode

    @property
    def reasoning_content(self):
        return self._reasoning_content

    @reasoning_content.setter
    def reasoning_content(self, value: str):
        self._reasoning_content = value

    @abstractmethod
    def __init__(self, config: LLMConfig):
        pass

    def _user_msg(self, msg: str, images: Optional[Union[str, list[str]]] = None) -> dict[str, Union[str, dict]]:
        if images and self.support_image_input():
            # as gpt-4v, chat with image
            return self._user_msg_with_imgs(msg, images)
        else:
            return {"role": "user", "content": msg}

    def _user_msg_with_imgs(self, msg: str, images: Optional[Union[str, list[str]]]):
        """
        images: can be list of http(s) url or base64
        """
        if isinstance(images, str):
            images = [images]
        content = [{"type": "text", "text": msg}]
        for image in images:
            # image url or image base64
            url = image if image.startswith("http") else f"data:image/jpeg;base64,{image}"
            # it can with multiple-image inputs
            content.append({"type": "image_url", "image_url": {"url": url}})
        return {"role": "user", "content": content}

    def _assistant_msg(self, msg: str) -> dict[str, str]:
        return {"role": "assistant", "content": msg}

    def _system_msg(self, msg: str) -> dict[str, str]:
        return {"role": "system", "content": msg}

    def support_image_input(self) -> bool:
        return any([m in self.config.model for m in MULTI_MODAL_MODELS])

    def format_msg(self, messages: Union[str, "Message", list[dict], list["Message"], list[str]]) -> list[dict]:
        """convert messages to list[dict]."""
        from metagpt.schema import Message

        if not isinstance(messages, list):
            messages = [messages]

        processed_messages = []
        for msg in messages:
            if isinstance(msg, str):
                processed_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict):
                assert set(msg.keys()) == set(["role", "content"])
                processed_messages.append(msg)
            elif isinstance(msg, Message):
                images = msg.metadata.get(IMAGES)
                processed_msg = self._user_msg(msg=msg.content, images=images) if images else msg.to_dict()
                processed_messages.append(processed_msg)
            else:
                raise ValueError(
                    f"Only support message type are: str, Message, dict, but got {type(messages).__name__}!"
                )
        return processed_messages

    def _system_msgs(self, msgs: list[str]) -> list[dict[str, str]]:
        return [self._system_msg(msg) for msg in msgs]

    def _default_system_msg(self):
        return self._system_msg(self.system_prompt)

    def _update_costs(self, usage: Union[dict, BaseModel], model: str = None, local_calc_usage: bool = True):
        """update each request's token cost
        Args:
            model (str): model name or in some scenarios called endpoint
            local_calc_usage (bool): some models don't calculate usage, it will overwrite LLMConfig.calc_usage
        """
        calc_usage = self.config.calc_usage and local_calc_usage
        model = model or self.pricing_plan
        model = model or self.model
        usage = usage.model_dump() if isinstance(usage, BaseModel) else usage
        if calc_usage and self.cost_manager and usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                self.cost_manager.update_cost(prompt_tokens, completion_tokens, model)
            except Exception as e:
                logger.error(f"{self.__class__.__name__} updates costs failed! exp: {e}")

    def get_costs(self) -> Costs:
        if not self.cost_manager:
            return Costs(0, 0, 0, 0)
        return self.cost_manager.get_costs()

    def mask_base64_data(self, msg: dict) -> dict:
        """Process the base64 image data in the message, replacing it with placeholders for easier logging

        Args:
            msg (dict): A dictionary of messages in OpenAI format

        Returns:
            dict: This is the processed message dictionary with the image data replaced with placeholders
        """
        if not isinstance(msg, dict):
            return msg

        new_msg = msg.copy()
        content = new_msg.get("content")
        img_base64_prefix = "data:image/"

        if isinstance(content, list):
            # Handling multimodal content (like gpt-4v format)
            new_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image_url":
                    image_url = item.get("image_url", {}).get("url", "")
                    if image_url.startswith(img_base64_prefix):
                        item = item.copy()
                        item["image_url"] = {"url": "<Image base64 data has been omitted>"}
                new_content.append(item)
            new_msg["content"] = new_content
        elif isinstance(content, str) and img_base64_prefix in content:
            # Process plain text messages containing base64 image data
            new_msg["content"] = "<Messages containing image base64 data have been omitted>"
        return new_msg

    async def aask(
        self,
        msg: Union[str, list[dict[str, str]]],
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        images: Optional[Union[str, list[str]]] = None,
        timeout=USE_CONFIG_TIMEOUT,
        stream=None,
    ) -> str:
        if system_msgs:
            message = self._system_msgs(system_msgs)
        else:
            message = [self._default_system_msg()]
        if not self.use_system_prompt:
            message = []
        if format_msgs:
            message.extend(format_msgs)
        if isinstance(msg, str):
            message.append(self._user_msg(msg, images=images))
        else:
            message.extend(msg)
        if stream is None:
            stream = self.config.stream

        # the image data is replaced with placeholders to avoid long output
        masked_message = [self.mask_base64_data(m) for m in message]
        logger.debug(masked_message)

        compressed_message = self.compress_messages(message, compress_type=self.config.compress_type)
        rsp = await self.acompletion_text(compressed_message, stream=stream, timeout=self.get_timeout(timeout))
        # rsp = await self.acompletion_text(message, stream=stream, timeout=self.get_timeout(timeout))
        return rsp

    def _extract_assistant_rsp(self, context):
        return "\n".join([i["content"] for i in context if i["role"] == "assistant"])

    async def aask_batch(self, msgs: list, timeout=USE_CONFIG_TIMEOUT) -> str:
        """Sequential questioning"""
        context = []
        for msg in msgs:
            umsg = self._user_msg(msg)
            context.append(umsg)
            rsp_text = await self.acompletion_text(context, timeout=self.get_timeout(timeout))
            context.append(self._assistant_msg(rsp_text))
        return self._extract_assistant_rsp(context)

    async def aask_code(
        self, messages: Union[str, "Message", list[dict]], timeout=USE_CONFIG_TIMEOUT, **kwargs
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        """_achat_completion implemented by inherited class"""

    @abstractmethod
    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        """Asynchronous version of completion
        All GPTAPIs are required to provide the standard OpenAI completion interface
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "hello, show me python hello world code"},
            # {"role": "assistant", "content": ...}, # If there is an answer in the history, also include it
        ]
        """

    @abstractmethod
    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        """_achat_completion_stream implemented by inherited class"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(min=1, max=60),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(ConnectionError),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(
        self, messages: list[dict], stream: bool = False, timeout: int = USE_CONFIG_TIMEOUT
    ) -> str:
        """Asynchronous version of completion. Return str. Support stream-print"""
        if stream:
            return await self._achat_completion_stream(messages, timeout=self.get_timeout(timeout))
        resp = await self._achat_completion(messages, timeout=self.get_timeout(timeout))
        return self.get_choice_text(resp)

    def get_choice_text(self, rsp: dict) -> str:
        """Required to provide the first text of choice"""
        message = rsp.get("choices")[0]["message"]
        if "reasoning_content" in message:
            self.reasoning_content = message["reasoning_content"]
        return message["content"]

    def get_choice_delta_text(self, rsp: dict) -> str:
        """Required to provide the first text of stream choice"""
        return rsp.get("choices", [{}])[0].get("delta", {}).get("content", "")

    def get_choice_function(self, rsp: dict) -> dict:
        """Required to provide the first function of choice
        :param dict rsp: OpenAI chat.comletion respond JSON, Note "message" must include "tool_calls",
            and "tool_calls" must include "function", for example:
            {...
                "choices": [
                    {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": null,
                        "tool_calls": [
                        {
                            "id": "call_Y5r6Ddr2Qc2ZrqgfwzPX5l72",
                            "type": "function",
                            "function": {
                            "name": "execute",
                            "arguments": "{\n  \"language\": \"python\",\n  \"code\": \"print('Hello, World!')\"\n}"
                            }
                        }
                        ]
                    },
                    "finish_reason": "stop"
                    }
                ],
                ...}
        :return dict: return first function of choice, for exmaple,
            {'name': 'execute', 'arguments': '{\n  "language": "python",\n  "code": "print(\'Hello, World!\')"\n}'}
        """
        return rsp.get("choices")[0]["message"]["tool_calls"][0]["function"]

    def get_choice_function_arguments(self, rsp: dict) -> dict:
        """Required to provide the first function arguments of choice.

        :param dict rsp: same as in self.get_choice_function(rsp)
        :return dict: return the first function arguments of choice, for example,
            {'language': 'python', 'code': "print('Hello, World!')"}
        """
        return json.loads(self.get_choice_function(rsp)["arguments"], strict=False)

    def messages_to_prompt(self, messages: list[dict]):
        """[{"role": "user", "content": msg}] to user: <msg> etc."""
        return "\n".join([f"{i['role']}: {i['content']}" for i in messages])

    def messages_to_dict(self, messages):
        """objects to [{"role": "user", "content": msg}] etc."""
        return [i.to_dict() for i in messages]

    def with_model(self, model: str):
        """Set model and return self. For example, `with_model("gpt-3.5-turbo")`."""
        self.config.model = model
        return self

    def get_timeout(self, timeout: int) -> int:
        return timeout or self.config.timeout or LLM_API_TIMEOUT

    def count_tokens(self, messages: list[dict]) -> int:
        # A very raw heuristic to count tokens, taking reference from:
        # https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
        # https://platform.deepseek.com/api-docs/#token--token-usage
        # The heuristics is a huge overestimate for English text, e.g., and should be overwrittem with accurate token count function in inherited class
        # logger.warning("Base count_tokens is not accurate and should be overwritten.")
        return sum([int(len(msg["content"]) * 0.5) for msg in messages])

    def compress_messages(
        self,
        messages: list[dict],
        compress_type: CompressType = CompressType.NO_COMPRESS,
        max_token: int = 128000,
        threshold: float = 0.8,
    ) -> list[dict]:
        """Compress messages to fit within the token limit.
        Args:
            messages (list[dict]): List of messages to compress.
            compress_type (CompressType, optional): Compression strategy. Defaults to CompressType.NO_COMPRESS.
            max_token (int, optional): Maximum token limit. Defaults to 128000. Not effective if token limit can be found in TOKEN_MAX.
            threshold (float): Token limit threshold. Defaults to 0.8. Reserve 20% of the token limit for completion message.
        """
        if compress_type == CompressType.NO_COMPRESS:
            return messages

        max_token = TOKEN_MAX.get(self.config.model, max_token)
        keep_token = int(max_token * threshold)
        compressed = []

        # Always keep system messages
        # NOTE: Assume they do not exceed token limit
        system_msg_val = self._system_msg("")["role"]
        system_msgs = []
        for i, msg in enumerate(messages):
            if msg["role"] == system_msg_val:
                system_msgs.append(msg)
            else:
                user_assistant_msgs = messages[i:]
                break
        # system_msgs = [msg for msg in messages if msg["role"] == system_msg_val]
        # user_assistant_msgs = [msg for msg in messages if msg["role"] != system_msg_val]
        compressed.extend(system_msgs)
        current_token_count = self.count_tokens(system_msgs)

        if compress_type in [CompressType.POST_CUT_BY_TOKEN, CompressType.POST_CUT_BY_MSG]:
            # Under keep_token constraint, keep as many latest messages as possible
            for i, msg in enumerate(reversed(user_assistant_msgs)):
                token_count = self.count_tokens([msg])
                if current_token_count + token_count <= keep_token:
                    compressed.insert(len(system_msgs), msg)
                    current_token_count += token_count
                else:
                    if compress_type == CompressType.POST_CUT_BY_TOKEN or len(compressed) == len(system_msgs):
                        # Truncate the message to fit within the remaining token count; Otherwise, discard the msg. If compressed has no user or assistant message, enforce cutting by token
                        truncated_content = msg["content"][-(keep_token - current_token_count) :]
                        compressed.insert(len(system_msgs), {"role": msg["role"], "content": truncated_content})
                    logger.warning(
                        f"Truncated messages with {compress_type} to fit within the token limit. "
                        f"The first user or assistant message after truncation (originally the {i}-th message from last): {compressed[len(system_msgs)]}."
                    )
                    break

        elif compress_type in [CompressType.PRE_CUT_BY_TOKEN, CompressType.PRE_CUT_BY_MSG]:
            # Under keep_token constraint, keep as many earliest messages as possible
            for i, msg in enumerate(user_assistant_msgs):
                token_count = self.count_tokens([msg])
                if current_token_count + token_count <= keep_token:
                    compressed.append(msg)
                    current_token_count += token_count
                else:
                    if compress_type == CompressType.PRE_CUT_BY_TOKEN or len(compressed) == len(system_msgs):
                        # Truncate the message to fit within the remaining token count; Otherwise, discard the msg. If compressed has no user or assistant message, enforce cutting by token
                        truncated_content = msg["content"][: keep_token - current_token_count]
                        compressed.append({"role": msg["role"], "content": truncated_content})
                    logger.warning(
                        f"Truncated messages with {compress_type} to fit within the token limit. "
                        f"The last user or assistant message after truncation (originally the {i}-th message): {compressed[-1]}."
                    )
                    break

        return compressed
