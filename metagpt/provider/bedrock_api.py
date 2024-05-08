#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anthropic import AsyncAnthropicBedrock
from anthropic.types import Message, Usage

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider


@register_provider([LLMType.BEDROCK])
class BedRockLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.__init_bedrock()

    def __init_bedrock(self):
        self.model = self.config.model
        self.aclient: AsyncAnthropicBedrock = AsyncAnthropicBedrock(
            aws_access_key=self.config.access_key,
            aws_secret_key=self.config.secret_key,
        )

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
        return kwargs

    def _update_costs(
        self, usage: Usage, model: str = None, local_calc_usage: bool = True
    ):
        updated_usage = {
            "prompt_tokens": usage.input_tokens,
            "completion_tokens": usage.output_tokens,
        }
        model = self._model_name_trim(model)
        super()._update_costs(updated_usage, model)
    
    def _model_name_trim(self, model: str) -> str:
        # "anthropic.claude-3-sonnet-20240229-v1:0" -> claude-3-sonnet-20240229
        head_trimed = model.split('.')[1]
        last_hyphen_index = head_trimed.rfind('-')
        return head_trimed[:last_hyphen_index]
        
    def get_choice_text(self, resp: Message) -> str:
        return resp.content[0].text

    async def _achat_completion(
        self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT
    ) -> Message:
        kwargs = self._const_kwargs(messages)
        resp: Message = await self.aclient.messages.create(
            timeout=timeout,
            **kwargs
        )
        self._update_costs(resp.usage, self.model)
        return resp

    async def acompletion(
        self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT
    ) -> Message:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(
        self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT
    ) -> str:
        kwargs = self._const_kwargs(messages)
        stream = await self.aclient.messages.create(
            timeout=timeout,
            **kwargs,
        )
        collected_content = []
        usage = Usage(input_tokens=0, output_tokens=0)
        async for event in stream:
            event_type = event.type
            if event_type == "message_start":
                usage.input_tokens = event.message.usage.input_tokens
                usage.output_tokens = event.message.usage.output_tokens
            elif event_type == "content_block_delta":
                content = event.delta.text
                log_llm_stream(content)
                collected_content.append(content)
            elif event_type == "message_delta":
                usage.output_tokens = (
                    event.usage.output_tokens
                )  # update final output_tokens

        log_llm_stream("\n")
        self._update_costs(usage, self.model)
        full_content = "".join(collected_content)
        return full_content
