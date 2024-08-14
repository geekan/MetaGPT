"""RAG LLM."""
import asyncio
from typing import Any

from llama_index.core.constants import DEFAULT_CONTEXT_WINDOW
from llama_index.core.llms import (
    CompletionResponse,
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback
from pydantic import Field, model_validator

from metagpt.config2 import Config
from metagpt.llm import LLM
from metagpt.provider.base_llm import BaseLLM
from metagpt.utils.async_helper import NestAsyncio
from metagpt.utils.token_counter import TOKEN_MAX


class RAGLLM(CustomLLM):
    """LlamaIndex's LLM is different from MetaGPT's LLM.

    Inherit CustomLLM from llamaindex, making MetaGPT's LLM can be used by LlamaIndex.
    """

    model_infer: BaseLLM = Field(..., description="The MetaGPT's LLM.")
    context_window: int = -1
    num_output: int = -1
    model_name: str = ""

    @model_validator(mode="after")
    def update_from_config(self):
        config = Config.default()
        if self.context_window < 0:
            self.context_window = TOKEN_MAX.get(config.llm.model, DEFAULT_CONTEXT_WINDOW)

        if self.num_output < 0:
            self.num_output = config.llm.max_token

        if not self.model_name:
            self.model_name = config.llm.model

        return self

    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(
            context_window=self.context_window, num_output=self.num_output, model_name=self.model_name or "unknown"
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        NestAsyncio.apply_once()
        return asyncio.get_event_loop().run_until_complete(self.acomplete(prompt, **kwargs))

    @llm_completion_callback()
    async def acomplete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        text = await self.model_infer.aask(msg=prompt, stream=False)
        return CompletionResponse(text=text)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        ...


def get_rag_llm(model_infer: BaseLLM = None) -> RAGLLM:
    """Get llm that can be used by LlamaIndex."""
    return RAGLLM(model_infer=model_infer or LLM())
