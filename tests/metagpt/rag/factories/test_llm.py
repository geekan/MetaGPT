import pytest
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.gemini import Gemini
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from metagpt.configs.llm_config import LLMType
from metagpt.rag.factories.llm import RAGLLMFactory


class TestRAGLLMFactory:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        # Mock the config object for all tests in this class
        self.mock_config = mocker.MagicMock()
        self.mock_config.llm.api_type = LLMType.OPENAI
        self.mock_config.llm.base_url = "http://example.com"
        self.mock_config.llm.api_key = "test_api_key"
        self.mock_config.llm.api_version = "v1"
        self.mock_config.llm.model = "test_model"
        self.mock_config.llm.max_token = 100
        self.mock_config.llm.temperature = 0.5
        mocker.patch("metagpt.rag.factories.llm.config", self.mock_config)
        self.factory = RAGLLMFactory()

    @pytest.mark.parametrize(
        "llm_type,expected_class",
        [
            (LLMType.OPENAI, OpenAI),
            (LLMType.AZURE, AzureOpenAI),
            (LLMType.GEMINI, Gemini),
            (LLMType.OLLAMA, Ollama),
        ],
    )
    def test_creates_correct_llm_instance(self, llm_type, expected_class, mocker):
        # Mock the LLM constructors
        mocker.patch.object(expected_class, "__init__", return_value=None)
        instance = self.factory.get_rag_llm(key=llm_type)
        assert isinstance(instance, expected_class)
        expected_class.__init__.assert_called_once()

    def test_uses_default_llm_type_when_no_key_provided(self, mocker):
        # Assume the default API type is OPENAI for this test
        mock = mocker.patch.object(OpenAI, "__init__", return_value=None)
        instance = self.factory.get_rag_llm()
        assert isinstance(instance, OpenAI)
        mock.assert_called_once_with(
            api_base=self.mock_config.llm.base_url,
            api_key=self.mock_config.llm.api_key,
            api_version=self.mock_config.llm.api_version,
            model=self.mock_config.llm.model,
            max_tokens=self.mock_config.llm.max_token,
            temperature=self.mock_config.llm.temperature,
        )
