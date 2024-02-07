import pytest
from llama_index import ServiceContext
from llama_index.indices.base import BaseIndex
from llama_index.postprocessor import LLMRerank

from metagpt.rag.factory import RankerFactory, RetrieverFactory
from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    FAISSRetrieverConfig,
    LLMRankerConfig,
)


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
        return mocker.patch("metagpt.rag.factory.FaissVectorStore")

    @pytest.fixture
    def mock_storage_context(self, mocker):
        return mocker.patch("metagpt.rag.factory.StorageContext")

    @pytest.fixture
    def mock_vector_store_index(self, mocker):
        return mocker.patch("metagpt.rag.factory.VectorStoreIndex")

    @pytest.fixture
    def mock_dynamic_bm25_retriever(self, mocker):
        mock = mocker.MagicMock(spec=DynamicBM25Retriever)
        return mocker.patch("metagpt.rag.factory.DynamicBM25Retriever", mock)

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


class TestRankerFactory:
    @pytest.fixture
    def mock_service_context(self, mocker):
        return mocker.MagicMock(spec=ServiceContext)

    def test_get_rankers_with_no_configs_returns_default_ranker(self, mock_service_context):
        # Setup
        factory = RankerFactory()

        # Execute
        rankers = factory.get_rankers(service_context=mock_service_context)

        # Assertions
        assert len(rankers) == 1
        assert isinstance(rankers[0], LLMRerank)

    def test_get_rankers_with_specific_config_returns_correct_ranker(self, mock_service_context):
        # Setup
        config = LLMRankerConfig(top_n=3)
        factory = RankerFactory()

        # Execute
        rankers = factory.get_rankers(configs=[config], service_context=mock_service_context)

        # Assertions
        assert len(rankers) == 1
        assert isinstance(rankers[0], LLMRerank)
        assert rankers[0].top_n == 3

    def test_get_rankers_with_unknown_config_raises_value_error(self, mocker, mock_service_context):
        # Mock
        mock_config = mocker.MagicMock()  # 使用 MagicMock 来模拟一个未知的配置类型

        # Setup
        factory = RankerFactory()

        # Execute & Assertions
        with pytest.raises(ValueError):
            factory.get_rankers(configs=[mock_config], service_context=mock_service_context)
