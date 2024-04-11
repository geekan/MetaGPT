import faiss
import pytest
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.elasticsearch import ElasticsearchStore

from metagpt.rag.factories.retriever import RetrieverFactory
from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever
from metagpt.rag.retrievers.chroma_retriever import ChromaRetriever
from metagpt.rag.retrievers.es_retriever import ElasticsearchRetriever
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    ChromaRetrieverConfig,
    ElasticsearchRetrieverConfig,
    ElasticsearchStoreConfig,
    FAISSRetrieverConfig,
)


class TestRetrieverFactory:
    @pytest.fixture(autouse=True)
    def retriever_factory(self):
        self.retriever_factory: RetrieverFactory = RetrieverFactory()

    @pytest.fixture
    def mock_faiss_index(self, mocker):
        return mocker.MagicMock(spec=faiss.IndexFlatL2)

    @pytest.fixture
    def mock_vector_store_index(self, mocker):
        mock = mocker.MagicMock(spec=VectorStoreIndex)
        mock._embed_model = mocker.MagicMock()
        mock.docstore.docs.values.return_value = []
        return mock

    @pytest.fixture
    def mock_chroma_vector_store(self, mocker):
        return mocker.MagicMock(spec=ChromaVectorStore)

    @pytest.fixture
    def mock_es_vector_store(self, mocker):
        return mocker.MagicMock(spec=ElasticsearchStore)

    def test_get_retriever_with_faiss_config(self, mock_faiss_index, mocker, mock_vector_store_index):
        mock_config = FAISSRetrieverConfig(dimensions=128)
        mocker.patch("faiss.IndexFlatL2", return_value=mock_faiss_index)
        mocker.patch.object(self.retriever_factory, "_extract_index", return_value=mock_vector_store_index)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config])

        assert isinstance(retriever, FAISSRetriever)

    def test_get_retriever_with_bm25_config(self, mocker, mock_vector_store_index):
        mock_config = BM25RetrieverConfig()
        mocker.patch("rank_bm25.BM25Okapi.__init__", return_value=None)
        mocker.patch.object(self.retriever_factory, "_extract_index", return_value=mock_vector_store_index)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config])

        assert isinstance(retriever, DynamicBM25Retriever)

    def test_get_retriever_with_multiple_configs_returns_hybrid(self, mocker, mock_vector_store_index):
        mock_faiss_config = FAISSRetrieverConfig(dimensions=128)
        mock_bm25_config = BM25RetrieverConfig()
        mocker.patch("rank_bm25.BM25Okapi.__init__", return_value=None)
        mocker.patch.object(self.retriever_factory, "_extract_index", return_value=mock_vector_store_index)

        retriever = self.retriever_factory.get_retriever(configs=[mock_faiss_config, mock_bm25_config])

        assert isinstance(retriever, SimpleHybridRetriever)

    def test_get_retriever_with_chroma_config(self, mocker, mock_vector_store_index, mock_chroma_vector_store):
        mock_config = ChromaRetrieverConfig(persist_path="/path/to/chroma", collection_name="test_collection")
        mock_chromadb = mocker.patch("metagpt.rag.factories.retriever.chromadb.PersistentClient")
        mock_chromadb.get_or_create_collection.return_value = mocker.MagicMock()
        mocker.patch("metagpt.rag.factories.retriever.ChromaVectorStore", return_value=mock_chroma_vector_store)
        mocker.patch.object(self.retriever_factory, "_extract_index", return_value=mock_vector_store_index)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config])

        assert isinstance(retriever, ChromaRetriever)

    def test_get_retriever_with_es_config(self, mocker, mock_vector_store_index, mock_es_vector_store):
        mock_config = ElasticsearchRetrieverConfig(store_config=ElasticsearchStoreConfig())
        mocker.patch("metagpt.rag.factories.retriever.ElasticsearchStore", return_value=mock_es_vector_store)
        mocker.patch.object(self.retriever_factory, "_extract_index", return_value=mock_vector_store_index)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config])

        assert isinstance(retriever, ElasticsearchRetriever)

    def test_create_default_retriever(self, mocker, mock_vector_store_index):
        mocker.patch.object(self.retriever_factory, "_extract_index", return_value=mock_vector_store_index)
        mock_vector_store_index.as_retriever = mocker.MagicMock()

        retriever = self.retriever_factory.get_retriever()

        mock_vector_store_index.as_retriever.assert_called_once()
        assert retriever is mock_vector_store_index.as_retriever.return_value

    def test_extract_index_from_config(self, mock_vector_store_index):
        mock_config = FAISSRetrieverConfig(index=mock_vector_store_index)

        extracted_index = self.retriever_factory._extract_index(config=mock_config)

        assert extracted_index == mock_vector_store_index

    def test_extract_index_from_kwargs(self, mock_vector_store_index):
        extracted_index = self.retriever_factory._extract_index(index=mock_vector_store_index)

        assert extracted_index == mock_vector_store_index
