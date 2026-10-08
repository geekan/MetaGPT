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
from typing import Any, Optional, Union

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
from metagpt.utils.cost_manager import CostManager, Costs, NoMoneyError
from metagpt.utils.token_counter import TOKEN_MAX
from metagpt.provider.rate_limiter import get_rate_limiter
from metagpt.provider.retry_policy import DEFAULT_RETRY_POLICY, RetryPolicy, with_retry
from metagpt.provider.token_usage import TokenUsageTracker, get_token_usage_tracker, normalize_usage
from metagpt.provider.context_manager import ContextManager
from metagpt.provider.tool_calling import to_openai_tools


class BaseLLM(ABC):
    """LLM API abstract class, requiring all inheritors to provide a series of standard capabilities"""

    config: LLMConfig
    use_system_prompt: bool = True
    system_prompt = "You are a helpful assistant."

    # OpenAI / Azure / Others
    aclient: Optional[Union[AsyncOpenAI]] = None
    cost_manager: Optional[CostManager] = None
    # Maintain model name in own instance in case the global config has changed,
    # Should always use model not config.model within this class
    model: Optional[str] = None
    pricing_plan: Optional[str] = None

    # Shared retry + rate-limit (MEO-compatible)
    retry_policy: Optional["RetryPolicy"] = None
    rate_limit_key: Optional[str] = None  # defaults to provider class name

    # Shared token usage tracking (MEO tokenUsage.js twin)
    token_usage: Optional[TokenUsageTracker] = None
    _last_usage: Optional[dict] = None

    # Shared context + tool calling (MEO twins)
    context_manager: Optional[ContextManager] = None

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
        return any([m in self.model for m in MULTI_MODAL_MODELS])

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

    def _update_costs(self, usage: Union[dict, BaseModel], model: str = None, local_calc_usage: bool = True, provider: str = ""):
        """update each request's token cost
        Args:
            model (str): model name or in some scenarios called endpoint
            local_calc_usage (bool): some models don't calculate usage, it will overwrite LLMConfig.calc_usage
            provider (str): optional provider tag for shared CostManager.by_provider
        """
        calc_usage = self.config.calc_usage and local_calc_usage
        model = model or self.pricing_plan
        model = model or self.model
        usage = usage.model_dump() if isinstance(usage, BaseModel) else usage
        if calc_usage and self.cost_manager and usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0) or 0)
                completion_tokens = int(usage.get("completion_tokens", 0) or usage.get("output_tokens", 0) or 0)
                provider_tag = provider or getattr(self, "provider_name", "") or self.__class__.__name__
                # Prefer shared updateCost when available (MEO-compatible interface)
                if hasattr(self.cost_manager, "updateCost"):
                    self.cost_manager.updateCost(
                        promptTokens=prompt_tokens,
                        completionTokens=completion_tokens,
                        model=model,
                        provider=provider_tag,
                    )
                else:
                    self.cost_manager.update_cost(prompt_tokens, completion_tokens, model)
                # Shared TokenUsage tracker (always, even if cost calc disabled elsewhere)
                tracker = self.token_usage or get_token_usage_tracker()
                self._last_usage = tracker.record(
                    promptTokens=prompt_tokens,
                    completionTokens=completion_tokens,
                    model=model,
                    provider=provider_tag,
                    usage=usage,
                )
            except Exception as e:
                logger.error(f"{self.__class__.__name__} updates costs failed! exp: {e}")

    @property
    def last_token_usage(self) -> Optional[dict]:
        """Normalized usage from the most recent call ({promptTokens, completionTokens, totalTokens})."""
        return self._last_usage

    def get_token_usage_totals(self) -> dict:
        tracker = self.token_usage or get_token_usage_tracker()
        return tracker.totals()

    def get_costs(self) -> Costs:
        if not self.cost_manager:
            return Costs(0, 0, 0, 0)
        return self.cost_manager.get_costs()

    def get_cost_snapshot(self) -> dict:
        """Shared MEO-compatible cost snapshot dict."""
        if not self.cost_manager:
            return CostManager().getCosts()
        if hasattr(self.cost_manager, "getCosts"):
            return self.cost_manager.getCosts()
        c = self.cost_manager.get_costs()
        return {
            "totalPromptTokens": c.total_prompt_tokens,
            "totalCompletionTokens": c.total_completion_tokens,
            "totalCost": c.total_cost,
            "maxBudget": c.total_budget,
            "remaining": max(0.0, c.total_budget - c.total_cost),
            "overBudget": c.total_cost >= c.total_budget,
        }

    def set_cost_manager(self, cost_manager: CostManager) -> None:
        """Attach / replace shared CostManager (same interface as MEO)."""
        self.cost_manager = cost_manager

    def check_budget(self) -> None:
        """Raise NoMoneyError if enforce_budget and over max_budget."""
        if self.cost_manager is None:
            return
        if hasattr(self.cost_manager, "checkBudget"):
            self.cost_manager.checkBudget()
        elif getattr(self.cost_manager, "enforce_budget", False):
            if self.cost_manager.total_cost >= self.cost_manager.max_budget:
                raise NoMoneyError(self.cost_manager.total_cost, self.cost_manager.max_budget)

    def set_budget(self, max_budget: float, enforce: Optional[bool] = None) -> dict:
        if self.cost_manager is None:
            self.cost_manager = CostManager()
        if hasattr(self.cost_manager, "setBudget"):
            return self.cost_manager.setBudget(max_budget, enforce=enforce)
        self.cost_manager.max_budget = float(max_budget)
        return self.get_cost_snapshot()

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

    async def aask_messages(
        self,
        messages: list[dict],
        tools: Optional[list] = None,
        tool_choice: Any = None,
        timeout=USE_CONFIG_TIMEOUT,
        stream: Optional[bool] = None,
        use_context_manager: bool = True,
    ) -> Any:
        """Chat with full message list + optional OpenAI tools (shared toolCalling interface).

        Returns raw provider response (dict / SDK object) so callers can parse tool_calls.
        Falls back to acompletion_text (string) if the provider has no tools-capable path.
        """
        msgs = [dict(m) for m in messages]
        if use_context_manager:
            ctx = self.context_manager or ContextManager()
            self.context_manager = ctx
            # sync context store with caller messages (non-system first)
            ctx.clear(keep_system=False)
            for m in msgs:
                ctx.add_message(m)
            msgs = ctx.messages()

        openai_tools = to_openai_tools(tools) if tools else None
        if stream is None:
            stream = self.config.stream and not openai_tools

        # Prefer subclass hook if present
        if hasattr(self, "_achat_completion_with_tools"):
            kwargs = {"timeout": self.get_timeout(timeout)}
            if openai_tools:
                kwargs["tools"] = openai_tools
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice
            self.check_budget()
            return await self._achat_completion_with_tools(msgs, **kwargs)

        # Default: text-only path (tools ignored by this provider)
        if openai_tools:
            logger.warning(f"[toolCalling] {self.__class__.__name__} has no tools path; degrading to text")
            names = ", ".join(t["function"]["name"] for t in openai_tools)
            msgs = list(msgs)
            if msgs:
                msgs[-1] = {
                    **msgs[-1],
                    "content": f"{msgs[-1].get('content', '')}\n\nAvailable tools: {names}",
                }
        text = await self.acompletion_text(msgs, stream=stream, timeout=self.get_timeout(timeout))
        return {"choices": [{"message": {"role": "assistant", "content": text}}]}

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

    def _provider_rate_key(self) -> str:
        return self.rate_limit_key or self.__class__.__name__

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
        """Asynchronous version of completion. Return str. Support stream-print.

        Applies shared RateLimiter + RetryPolicy (429-aware) before hitting the provider.
        """
        self.check_budget()
        limiter = get_rate_limiter()
        key = self._provider_rate_key()
        gate = await limiter.acquire(key)
        if not gate.get("allowed"):
            logger.warning(f"[rateLimiter] acquire failed key={key} after wait; proceeding carefully")
        try:
            policy = self.retry_policy or DEFAULT_RETRY_POLICY

            async def _call() -> str:
                if stream:
                    return await self._achat_completion_stream(messages, timeout=self.get_timeout(timeout))
                resp = await self._achat_completion(messages, timeout=self.get_timeout(timeout))
                return self.get_choice_text(resp)

            return await with_retry(_call, policy=policy)
        finally:
            limiter.release(key)

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
        self.model = model
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

        max_token = TOKEN_MAX.get(self.model, max_token)
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
