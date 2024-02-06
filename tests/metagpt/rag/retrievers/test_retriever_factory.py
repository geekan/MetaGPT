import pytest
from llama_index.indices.base import BaseIndex

from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever
from metagpt.rag.retrievers.factory import RetrieverFactory
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.schema import BM25RetrieverConfig, FAISSRetrieverConfig


class TestRetrieverFactory:
    @pytest.fixture
    def mock_base_index(self, mocker):
        mock = mocker.MagicMock(spec=BaseIndex)
        mock.as_retriever.return_value = mocker.MagicMock(spec=RAGRetriever)
        mock.service_context = mocker.MagicMock()
        mock.docstore.docs.values.return_value = []
        return mock

    @pytest.fixture
    def mock_faiss_retriever_config(self):
        return FAISSRetrieverConfig(dimensions=128)

    @pytest.fixture
    def mock_bm25_retriever_config(self):
        return BM25RetrieverConfig()

    @pytest.fixture
    def mock_faiss_vector_store(self, mocker):
        return mocker.patch("metagpt.rag.retrievers.factory.FaissVectorStore")

    @pytest.fixture
    def mock_storage_context(self, mocker):
        return mocker.patch("metagpt.rag.retrievers.factory.StorageContext")

    @pytest.fixture
    def mock_vector_store_index(self, mocker):
        return mocker.patch("metagpt.rag.retrievers.factory.VectorStoreIndex")

    @pytest.fixture
    def mock_dynamic_bm25_retriever(self, mocker):
        mock = mocker.MagicMock(spec=DynamicBM25Retriever)
        return mocker.patch("metagpt.rag.retrievers.factory.DynamicBM25Retriever", mock)

    def test_get_retriever_with_no_configs_returns_default_retriever(self, mock_base_index):
        factory = RetrieverFactory()
        retriever = factory.get_retriever(index=mock_base_index)
        assert isinstance(retriever, RAGRetriever)

    def test_get_retriever_with_specific_config_returns_correct_retriever(
        self,
        mock_base_index,
        mock_faiss_retriever_config,
        mock_faiss_vector_store,
        mock_storage_context,
        mock_vector_store_index,
    ):
        factory = RetrieverFactory()
        retriever = factory.get_retriever(index=mock_base_index, configs=[mock_faiss_retriever_config])
        assert isinstance(retriever, FAISSRetriever)

    def test_get_retriever_with_multiple_configs_returns_hybrid_retriever(
        self,
        mock_base_index,
        mock_faiss_retriever_config,
        mock_bm25_retriever_config,
        mock_faiss_vector_store,
        mock_storage_context,
        mock_vector_store_index,
        mock_dynamic_bm25_retriever,
    ):
        factory = RetrieverFactory()
        retriever = factory.get_retriever(
            index=mock_base_index, configs=[mock_faiss_retriever_config, mock_bm25_retriever_config]
        )
        assert isinstance(retriever, SimpleHybridRetriever)

    def test_get_retriever_with_unknown_config_raises_value_error(self, mock_base_index, mocker):
        mock_unknown_config = mocker.MagicMock()
        factory = RetrieverFactory()
        with pytest.raises(ValueError):
            factory.get_retriever(index=mock_base_index, configs=[mock_unknown_config])
