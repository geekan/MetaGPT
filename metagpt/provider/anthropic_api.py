#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anthropic import AsyncAnthropic
from anthropic.types import Message, Usage

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider


@register_provider([LLMType.ANTHROPIC, LLMType.CLAUDE])
class AnthropicLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.__init_anthropic()

    def __init_anthropic(self):
        self.model = self.config.model
        self.aclient: AsyncAnthropic = AsyncAnthropic(api_key=self.config.api_key, base_url=self.config.base_url)

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.config.max_token,
            "stream": stream,
        }
        if self.use_system_prompt:
            # if the model support system prompt, extract and pass it
            if messages[0]["role"] == "system":
                kwargs["messages"] = messages[1:]
                kwargs["system"] = messages[0]["content"]  # set system prompt here
        if self.config.reasoning:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.config.reasoning_max_token}
        return kwargs

    def _update_costs(self, usage: Usage, model: str = None, local_calc_usage: bool = True):
        usage = {"prompt_tokens": usage.input_tokens, "completion_tokens": usage.output_tokens}
        super()._update_costs(usage, model)

    def get_choice_text(self, resp: Message) -> str:
        if len(resp.content) > 1:
            self.reasoning_content = resp.content[0].thinking
            text = resp.content[1].text
        else:
            text = resp.content[0].text
        return text

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> Message:
        resp: Message = await self.aclient.messages.create(**self._const_kwargs(messages))
        self._update_costs(resp.usage, self.model)
        return resp

    async def acompletion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> Message:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        stream = await self.aclient.messages.create(**self._const_kwargs(messages, stream=True))
        collected_content = []
        collected_reasoning_content = []
        usage = Usage(input_tokens=0, output_tokens=0)
        async for event in stream:
            event_type = event.type
            if event_type == "message_start":
                usage.input_tokens = event.message.usage.input_tokens
                usage.output_tokens = event.message.usage.output_tokens
            elif event_type == "content_block_delta":
                delta_type = event.delta.type
                if delta_type == "thinking_delta":
                    collected_reasoning_content.append(event.delta.thinking)
                elif delta_type == "text_delta":
                    content = event.delta.text
                    log_llm_stream(content)
                    collected_content.append(content)
            elif event_type == "message_delta":
                usage.output_tokens = event.usage.output_tokens  # update final output_tokens

        log_llm_stream("\n")
        self._update_costs(usage)
        full_content = "".join(collected_content)
        if collected_reasoning_content:
            self.reasoning_content = "".join(collected_reasoning_content)
        return full_content
