import pytest
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Node

from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever


class TestDynamicBM25Retriever:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.doc1 = mocker.MagicMock(spec=Node)
        self.doc1.get_content.return_value = "Document content 1"
        self.doc2 = mocker.MagicMock(spec=Node)
        self.doc2.get_content.return_value = "Document content 2"
        self.mock_nodes = [self.doc1, self.doc2]

        index = mocker.MagicMock(spec=VectorStoreIndex)
        index.storage_context.persist.return_value = "ok"

        mock_nodes = []
        mock_tokenizer = mocker.MagicMock()
        self.mock_bm25okapi = mocker.patch("rank_bm25.BM25Okapi.__init__", return_value=None)

        self.retriever = DynamicBM25Retriever(nodes=mock_nodes, tokenizer=mock_tokenizer, index=index)

    def test_add_docs_updates_nodes_and_corpus(self):
        # Exec
        self.retriever.add_nodes(self.mock_nodes)

        # Assert
        assert len(self.retriever._nodes) == len(self.mock_nodes)
        assert len(self.retriever._corpus) == len(self.mock_nodes)
        self.retriever._tokenizer.assert_called()
        self.mock_bm25okapi.assert_called()

    def test_persist(self):
        self.retriever.persist("")
