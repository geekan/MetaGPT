import pytest

from metagpt.configs.llm_config import LLMType
from metagpt.rag.factories.embedding import RAGEmbeddingFactory


class TestRAGEmbeddingFactory:
    @pytest.fixture(autouse=True)
    def mock_embedding_factory(self):
        self.embedding_factory = RAGEmbeddingFactory()

    @pytest.fixture
    def mock_openai_embedding(self, mocker):
        return mocker.patch("metagpt.rag.factories.embedding.OpenAIEmbedding")

    @pytest.fixture
    def mock_azure_embedding(self, mocker):
        return mocker.patch("metagpt.rag.factories.embedding.AzureOpenAIEmbedding")

    def test_get_rag_embedding_openai(self, mock_openai_embedding):
        # Exec
        self.embedding_factory.get_rag_embedding(LLMType.OPENAI)

        # Assert
        mock_openai_embedding.assert_called_once()

    def test_get_rag_embedding_azure(self, mock_azure_embedding):
        # Exec
        self.embedding_factory.get_rag_embedding(LLMType.AZURE)

        # Assert
        mock_azure_embedding.assert_called_once()

    def test_get_rag_embedding_default(self, mocker, mock_openai_embedding):
        # Mock
        mock_config = mocker.patch("metagpt.rag.factories.embedding.config")
        mock_config.llm.api_type = LLMType.OPENAI

        # Exec
        self.embedding_factory.get_rag_embedding()

        # Assert
        mock_openai_embedding.assert_called_once()
