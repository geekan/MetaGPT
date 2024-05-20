from openai import AsyncStream
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from metagpt.provider.openai_api import OpenAILLM
from metagpt.configs.llm_config import LLMType
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream

@register_provider(LLMType.ARK)
class ArkLLM(OpenAILLM):
    """
    用于火山方舟的API
    见：https://www.volcengine.com/docs/82379/1263482
    """
    
    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> str:
        response: AsyncStream[ChatCompletionChunk] = await self.aclient.chat.completions.create(
            **self._cons_kwargs(messages, timeout=self.get_timeout(timeout)), 
            stream=True,
            extra_body={"stream_options": {"include_usage": True}}
        )
        usage = None
        collected_messages = []
        async for chunk in response:
            chunk_message = chunk.choices[0].delta.content or "" if chunk.choices else ""  # extract the message
            log_llm_stream(chunk_message)
            collected_messages.append(chunk_message)
            if chunk.usage:
                # the usage of ark when streaming is in the last chunk while others are null
                usage=CompletionUsage(**chunk.usage)

        log_llm_stream("\n")
        full_reply_content = "".join(collected_messages)
        self._update_costs(usage,chunk.model)
        return full_reply_content
    
    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> ChatCompletion:
        kwargs = self._cons_kwargs(messages, timeout=self.get_timeout(timeout))
        rsp: ChatCompletion = await self.aclient.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage,rsp.model)
        return rsp
