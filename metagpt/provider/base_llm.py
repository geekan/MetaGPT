#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/5 23:04
# @Author  : alexanderwu
# @File    : base_llm.py
# @Desc    : mashenquan, 2023/8/22. + try catch

import json
from abc import ABC, abstractmethod
from typing import Optional, Union

from openai import AsyncOpenAI

from metagpt.configs.llm_config import LLMConfig
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.cost_manager import CostManager


class BaseLLM(ABC):
    """LLM API abstract class, requiring all inheritors to provide a series of standard capabilities.

    Attributes:
        config: Configuration for the LLM.
        use_system_prompt: A boolean indicating if the system prompt should be used.
        system_prompt: The default system prompt.
        aclient: An optional asynchronous client for making API calls.
        cost_manager: An optional CostManager instance for managing API call costs.
        model: An optional model name string.
    """

    config: LLMConfig
    use_system_prompt: bool = True
    system_prompt = "You are a helpful assistant."

    # OpenAI / Azure / Others
    aclient: Optional[Union[AsyncOpenAI]] = None
    cost_manager: Optional[CostManager] = None
    model: Optional[str] = None

    @abstractmethod
    def __init__(self, config: LLMConfig):
        """Initializes the BaseLLM with a given configuration.

        Args:
            config: The configuration for the LLM.
        """
        pass

    def _user_msg(self, msg: str, images: Optional[Union[str, list[str]]] = None) -> dict[str, Union[str, dict]]:
        if images:
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
            content.append({"type": "image_url", "image_url": url})
        return {"role": "user", "content": content}

    def _assistant_msg(self, msg: str) -> dict[str, str]:
        return {"role": "assistant", "content": msg}

    def _system_msg(self, msg: str) -> dict[str, str]:
        return {"role": "system", "content": msg}

    def _system_msgs(self, msgs: list[str]) -> list[dict[str, str]]:
        return [self._system_msg(msg) for msg in msgs]

    def _default_system_msg(self):
        return self._system_msg(self.system_prompt)

    async def aask(
        self,
        msg: str,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        images: Optional[Union[str, list[str]]] = None,
        timeout=3,
        stream=True,
    ) -> str:
        """Asynchronously asks a question and returns the response.

        Args:
            msg: The message to ask.
            system_msgs: Optional list of system messages to prepend.
            format_msgs: Optional list of formatted messages to include.
            timeout: The timeout for the request.
            stream: Whether to stream the response.

        Returns:
            The response as a string.
        """
        if system_msgs:
            message = self._system_msgs(system_msgs)
        else:
            message = [self._default_system_msg()]
        if not self.use_system_prompt:
            message = []
        if format_msgs:
            message.extend(format_msgs)
        message.append(self._user_msg(msg, images=images))
        logger.debug(message)
        rsp = await self.acompletion_text(message, stream=stream, timeout=timeout)
        return rsp

    def _extract_assistant_rsp(self, context):
        return "\n".join([i["content"] for i in context if i["role"] == "assistant"])

    async def aask_batch(self, msgs: list, timeout=3) -> str:
        """Sequentially asks a list of questions and returns the concatenated assistant responses.

        Args:
            msgs: A list of messages to ask.
            timeout: The timeout for each request.

        Returns:
            A string containing the concatenated responses from the assistant.
        """
        context = []
        for msg in msgs:
            umsg = self._user_msg(msg)
            context.append(umsg)
            rsp_text = await self.acompletion_text(context, timeout=timeout)
            context.append(self._assistant_msg(rsp_text))
        return self._extract_assistant_rsp(context)

    async def aask_code(self, messages: Union[str, Message, list[dict]], timeout=3) -> dict:
        """Asks for code related to the given messages and returns the response.

        Args:
            messages: The messages to base the code request on.
            timeout: The timeout for the request.

        Returns:
            The response as a dictionary.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError

    @abstractmethod
    async def acompletion(self, messages: list[dict], timeout=3):
        """Asynchronous version of completion, requiring implementation in inheritors.

        Args:
            messages: A list of message dictionaries to process.
            timeout: The timeout for the request.
        """

    @abstractmethod
    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        """Asynchronously completes the given messages and returns the text response.

        Args:
            messages: A list of message dictionaries to complete.
            stream: Whether to stream the response.
            timeout: The timeout for the request.

        Returns:
            The text response as a string.
        """

    def get_choice_text(self, rsp: dict) -> str:
        """Extracts and returns the first text of choice from the response.

        Args:
            rsp: The response dictionary.

        Returns:
            The first text of choice.
        """
        return rsp.get("choices")[0]["message"]["content"]

    def get_choice_delta_text(self, rsp: dict) -> str:
        """Extracts and returns the first text of stream choice from the response.

        Args:
            rsp: The response dictionary.

        Returns:
            The first text of stream choice.
        """
        return rsp.get("choices", [{}])[0].get("delta", {}).get("content", "")

    def get_choice_function(self, rsp: dict) -> dict:
        """Extracts and returns the first function of choice from the response.

        Args:
            rsp: The response dictionary.

        Returns:
            The first function of choice as a dictionary.
        """
        return rsp.get("choices")[0]["message"]["tool_calls"][0]["function"]

    def get_choice_function_arguments(self, rsp: dict) -> dict:
        """Extracts and returns the first function arguments of choice from the response.

        Args:
            rsp: The response dictionary.

        Returns:
            The first function arguments of choice as a dictionary.
        """
        return json.loads(self.get_choice_function(rsp)["arguments"], strict=False)

    def messages_to_prompt(self, messages: list[dict]):
        """[{"role": "user", "content": msg}] to user: <msg> etc."""
        return "\n".join([f"{i['role']}: {i['content']}" for i in messages])

    def messages_to_dict(self, messages):
        """objects to [{"role": "user", "content": msg}] etc."""
        return [i.to_dict() for i in messages]
