import pytest
from llama_index.core.embeddings import MockEmbedding

from metagpt.rag.factories.index import RAGIndexFactory
from metagpt.rag.schema import (
    BM25IndexConfig,
    ChromaIndexConfig,
    ElasticsearchIndexConfig,
    ElasticsearchStoreConfig,
    FAISSIndexConfig,
)


class TestRAGIndexFactory:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.index_factory = RAGIndexFactory()

    @pytest.fixture
    def faiss_config(self):
        return FAISSIndexConfig(persist_path="")

    @pytest.fixture
    def chroma_config(self):
        return ChromaIndexConfig(persist_path="", collection_name="")

    @pytest.fixture
    def bm25_config(self):
        return BM25IndexConfig(persist_path="")

    @pytest.fixture
    def es_config(self, mocker):
        return ElasticsearchIndexConfig(store_config=ElasticsearchStoreConfig())

    @pytest.fixture
    def mock_storage_context(self, mocker):
        return mocker.patch("metagpt.rag.factories.index.StorageContext.from_defaults")

    @pytest.fixture
    def mock_load_index_from_storage(self, mocker):
        return mocker.patch("metagpt.rag.factories.index.load_index_from_storage")

    @pytest.fixture
    def mock_from_vector_store(self, mocker):
        return mocker.patch("metagpt.rag.factories.index.VectorStoreIndex.from_vector_store")

    @pytest.fixture
    def mock_embedding(self):
        return MockEmbedding(embed_dim=1)

    def test_create_faiss_index(
        self, mocker, faiss_config, mock_storage_context, mock_load_index_from_storage, mock_embedding
    ):
        # Mock
        mock_faiss_store = mocker.patch("metagpt.rag.factories.index.FaissVectorStore.from_persist_dir")

        # Exec
        self.index_factory.get_index(faiss_config, embed_model=mock_embedding)

        # Assert
        mock_faiss_store.assert_called_once()

    def test_create_bm25_index(
        self, mocker, bm25_config, mock_storage_context, mock_load_index_from_storage, mock_embedding
    ):
        self.index_factory.get_index(bm25_config, embed_model=mock_embedding)

    def test_create_chroma_index(self, mocker, chroma_config, mock_from_vector_store, mock_embedding):
        # Mock
        mock_chroma_db = mocker.patch("metagpt.rag.factories.index.chromadb.PersistentClient")
        mock_chroma_db.get_or_create_collection.return_value = mocker.MagicMock()

        mock_chroma_store = mocker.patch("metagpt.rag.factories.index.ChromaVectorStore")

        # Exec
        self.index_factory.get_index(chroma_config, embed_model=mock_embedding)

        # Assert
        mock_chroma_store.assert_called_once()

    def test_create_es_index(self, mocker, es_config, mock_from_vector_store, mock_embedding):
        # Mock
        mock_es_store = mocker.patch("metagpt.rag.factories.index.ElasticsearchStore")

        # Exec
        self.index_factory.get_index(es_config, embed_model=mock_embedding)

        # Assert
        mock_es_store.assert_called_once()
