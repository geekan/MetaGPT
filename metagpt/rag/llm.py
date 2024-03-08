"""RAG LLM."""
from typing import Any

from llama_index.core.llms import (
    CompletionResponse,
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback

from metagpt.config2 import config
from metagpt.llm import LLM
from metagpt.provider.base_llm import BaseLLM
from metagpt.utils.async_helper import run_coroutine_in_new_loop


class RAGLLM(CustomLLM):
    """LlamaIndex's LLM is different from MetaGPT's LLM.

    Inherit CustomLLM from llamaindex, making MetaGPT's LLM can be used by LlamaIndex.
    """

    model_infer: BaseLLM
    model_name: str = config.llm.model

    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(model_name=self.model_name)

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        return run_coroutine_in_new_loop(self.acomplete(prompt, **kwargs))

    @llm_completion_callback()
    async def acomplete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        text = await self.model_infer.aask(msg=prompt, stream=False)
        return CompletionResponse(text=text)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        ...


def get_rag_llm(model_infer: BaseLLM = None):
    """Get llm that can be used by LlamaIndex."""
    return RAGLLM(model_infer=model_infer or LLM())
