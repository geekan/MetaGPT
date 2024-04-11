from typing import Optional, Union

import pytest
from llama_index.core.llms import LLMMetadata

from metagpt.configs.llm_config import LLMConfig
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.provider.base_llm import BaseLLM
from metagpt.rag.factories.llm import RAGLLM, get_rag_llm


class MockLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        ...

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        """_achat_completion implemented by inherited class"""

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        return "ok"

    def completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        return "ok"

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        """_achat_completion_stream implemented by inherited class"""

    async def aask(
        self,
        msg: Union[str, list[dict[str, str]]],
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        images: Optional[Union[str, list[str]]] = None,
        timeout=USE_CONFIG_TIMEOUT,
        stream=True,
    ) -> str:
        return "ok"


class TestRAGLLM:
    @pytest.fixture
    def mock_model_infer(self):
        return MockLLM(config=LLMConfig())

    @pytest.fixture
    def rag_llm(self, mock_model_infer):
        return RAGLLM(model_infer=mock_model_infer)

    def test_metadata(self, rag_llm):
        metadata = rag_llm.metadata
        assert isinstance(metadata, LLMMetadata)
        assert metadata.context_window == rag_llm.context_window
        assert metadata.num_output == rag_llm.num_output
        assert metadata.model_name == rag_llm.model_name

    @pytest.mark.asyncio
    async def test_acomplete(self, rag_llm, mock_model_infer):
        response = await rag_llm.acomplete("question")
        assert response.text == "ok"

    def test_complete(self, rag_llm, mock_model_infer):
        response = rag_llm.complete("question")
        assert response.text == "ok"

    def test_stream_complete(self, rag_llm, mock_model_infer):
        rag_llm.stream_complete("question")


def test_get_rag_llm():
    result = get_rag_llm(MockLLM(config=LLMConfig()))
    assert isinstance(result, RAGLLM)
