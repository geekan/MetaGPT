import pytest

from metagpt.configs.embedding_config import EmbeddingType
from metagpt.configs.llm_config import LLMType
from metagpt.rag.factories.embedding import RAGEmbeddingFactory


class TestRAGEmbeddingFactory:
    @pytest.fixture(autouse=True)
    def mock_embedding_factory(self):
        self.embedding_factory = RAGEmbeddingFactory()

    @pytest.fixture
    def mock_config(self, mocker):
        return mocker.patch("metagpt.rag.factories.embedding.config")

    @staticmethod
    def mock_openai_embedding(mocker):
        return mocker.patch("metagpt.rag.factories.embedding.OpenAIEmbedding")

    @staticmethod
    def mock_azure_embedding(mocker):
        return mocker.patch("metagpt.rag.factories.embedding.AzureOpenAIEmbedding")

    @staticmethod
    def mock_gemini_embedding(mocker):
        return mocker.patch("metagpt.rag.factories.embedding.GeminiEmbedding")

    @staticmethod
    def mock_ollama_embedding(mocker):
        return mocker.patch("metagpt.rag.factories.embedding.OllamaEmbedding")

    @pytest.mark.parametrize(
        ("mock_func", "embedding_type"),
        [
            (mock_openai_embedding, LLMType.OPENAI),
            (mock_azure_embedding, LLMType.AZURE),
            (mock_openai_embedding, EmbeddingType.OPENAI),
            (mock_azure_embedding, EmbeddingType.AZURE),
            (mock_gemini_embedding, EmbeddingType.GEMINI),
            (mock_ollama_embedding, EmbeddingType.OLLAMA),
        ],
    )
    def test_get_rag_embedding(self, mock_func, embedding_type, mocker):
        # Mock
        mock = mock_func(mocker)

        # Exec
        self.embedding_factory.get_rag_embedding(embedding_type)

        # Assert
        mock.assert_called_once()

    def test_get_rag_embedding_default(self, mocker, mock_config):
        # Mock
        mock_openai_embedding = self.mock_openai_embedding(mocker)

        mock_config.embedding.api_type = None
        mock_config.llm.api_type = LLMType.OPENAI

        # Exec
        self.embedding_factory.get_rag_embedding()

        # Assert
        mock_openai_embedding.assert_called_once()

    @pytest.mark.parametrize(
        "model, embed_batch_size, expected_params",
        [("test_model", 100, {"model_name": "test_model", "embed_batch_size": 100}), (None, None, {})],
    )
    def test_try_set_model_and_batch_size(self, mock_config, model, embed_batch_size, expected_params):
        # Mock
        mock_config.embedding.model = model
        mock_config.embedding.embed_batch_size = embed_batch_size

        # Setup
        test_params = {}

        # Exec
        self.embedding_factory._try_set_model_and_batch_size(test_params)

        # Assert
        assert test_params == expected_params

    def test_resolve_embedding_type(self, mock_config):
        # Mock
        mock_config.embedding.api_type = EmbeddingType.OPENAI

        # Exec
        embedding_type = self.embedding_factory._resolve_embedding_type()

        # Assert
        assert embedding_type == EmbeddingType.OPENAI

    def test_resolve_embedding_type_exception(self, mock_config):
        # Mock
        mock_config.embedding.api_type = None
        mock_config.llm.api_type = LLMType.GEMINI

        # Assert
        with pytest.raises(TypeError):
            self.embedding_factory._resolve_embedding_type()

    def test_raise_for_key(self):
        with pytest.raises(ValueError):
            self.embedding_factory._raise_for_key("key")
