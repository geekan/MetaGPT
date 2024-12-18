import os

import faiss
import pytest
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.indices.property_graph import PGRetriever
from llama_index.core.schema import TextNode
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.vector_stores.milvus import MilvusVectorStore

from metagpt.rag.factories.retriever import RetrieverFactory
from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever
from metagpt.rag.retrievers.chroma_retriever import ChromaRetriever
from metagpt.rag.retrievers.es_retriever import ElasticsearchRetriever
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.retrievers.milvus_retriever import MilvusRetriever
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    ChromaRetrieverConfig,
    ElasticsearchRetrieverConfig,
    ElasticsearchStoreConfig,
    FAISSRetrieverConfig,
    MilvusRetrieverConfig,
    Neo4jPGRetrieverConfig,
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
    def mock_milvus_vector_store(self, mocker):
        return mocker.MagicMock(spec=MilvusVectorStore)

    @pytest.fixture
    def mock_es_vector_store(self, mocker):
        return mocker.MagicMock(spec=ElasticsearchStore)

    @pytest.fixture
    def mock_neo4j_pg_store(self, mocker):
        return mocker.MagicMock(spec=Neo4jPropertyGraphStore)

    @pytest.fixture
    def mock_nodes(self, mocker):
        return [TextNode(text="msg")]

    @pytest.fixture
    def mock_embedding(self):
        return MockEmbedding(embed_dim=1)

    def test_get_retriever_with_faiss_config(self, mock_faiss_index, mocker, mock_vector_store_index):
        mock_config = FAISSRetrieverConfig(dimensions=128)
        mocker.patch("faiss.IndexFlatL2", return_value=mock_faiss_index)
        mocker.patch.object(self.retriever_factory, "_extract_index", return_value=mock_vector_store_index)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config])

        assert isinstance(retriever, FAISSRetriever)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config], build_graph=True)
        assert isinstance(retriever, SimpleHybridRetriever)

    def test_get_retriever_with_bm25_config(self, mocker, mock_nodes):
        mock_config = BM25RetrieverConfig()
        mocker.patch("rank_bm25.BM25Okapi.__init__", return_value=None)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config], nodes=mock_nodes)

        assert isinstance(retriever, DynamicBM25Retriever)

    def test_get_retriever_with_multiple_configs_returns_hybrid(
        self, mocker, mock_nodes, mock_neo4j_pg_store, mock_embedding
    ):
        mock_faiss_config = FAISSRetrieverConfig(dimensions=1)
        mock_neo4j_pg_config = Neo4jPGRetrieverConfig()
        mock_bm25_config = BM25RetrieverConfig()
        mocker.patch("rank_bm25.BM25Okapi.__init__", return_value=None)
        mocker.patch("metagpt.rag.factories.retriever.Neo4jPropertyGraphStore", return_value=mock_neo4j_pg_store)

        retriever = self.retriever_factory.get_retriever(
            configs=[mock_faiss_config, mock_bm25_config], nodes=mock_nodes, embed_model=mock_embedding
        )

        assert isinstance(retriever, SimpleHybridRetriever)

        os.environ.setdefault("IS_TESTING", "test")  # use MockLLM
        retriever = self.retriever_factory.get_retriever(
            configs=[mock_faiss_config, mock_neo4j_pg_config], nodes=mock_nodes, embed_model=mock_embedding
        )
        assert isinstance(retriever, SimpleHybridRetriever)

    def test_get_retriever_with_chroma_config(self, mocker, mock_chroma_vector_store, mock_embedding):
        mock_config = ChromaRetrieverConfig(persist_path="/path/to/chroma", collection_name="test_collection")
        mock_chromadb = mocker.patch("metagpt.rag.factories.retriever.chromadb.PersistentClient")
        mock_chromadb.get_or_create_collection.return_value = mocker.MagicMock()
        mocker.patch("metagpt.rag.factories.retriever.ChromaVectorStore", return_value=mock_chroma_vector_store)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config], nodes=[], embed_model=mock_embedding)

        assert isinstance(retriever, ChromaRetriever)

    def test_get_retriever_with_milvus_config(self, mocker, mock_milvus_vector_store, mock_embedding):
        mock_config = MilvusRetrieverConfig(uri="/path/to/milvus.db", collection_name="test_collection")
        mocker.patch("metagpt.rag.factories.retriever.MilvusVectorStore", return_value=mock_milvus_vector_store)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config], nodes=[], embed_model=mock_embedding)

        assert isinstance(retriever, MilvusRetriever)

    def test_get_retriever_with_es_config(self, mocker, mock_es_vector_store, mock_embedding):
        mock_config = ElasticsearchRetrieverConfig(store_config=ElasticsearchStoreConfig())
        mocker.patch("metagpt.rag.factories.retriever.ElasticsearchStore", return_value=mock_es_vector_store)

        retriever = self.retriever_factory.get_retriever(configs=[mock_config], nodes=[], embed_model=mock_embedding)

        assert isinstance(retriever, ElasticsearchRetriever)

    def test_get_retriever_with_neo4j_pg_config(self, mocker, mock_neo4j_pg_store, mock_embedding):
        mock_config = Neo4jPGRetrieverConfig()
        mocker.patch("metagpt.rag.factories.retriever.Neo4jPropertyGraphStore", return_value=mock_neo4j_pg_store)
        os.environ.setdefault("IS_TESTING", "test")  # use MockLLM

        retriever = self.retriever_factory.get_retriever(configs=[mock_config], nodes=[], embed_model=mock_embedding)

        assert isinstance(retriever, PGRetriever)

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

    def test_get_or_build_when_get(self, mocker):
        want = "existing_index"
        mocker.patch.object(self.retriever_factory, "_extract_index", return_value=want)

        got = self.retriever_factory._build_es_index(None)

        assert got == want

    def test_get_or_build_when_build(self, mocker):
        want = "call_build_es_index"
        mocker.patch.object(self.retriever_factory, "_build_es_index", return_value=want)

        got = self.retriever_factory._build_es_index(None)

        assert got == want
