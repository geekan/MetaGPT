import pytest
from llama_index.core.schema import Node

from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever


class TestFAISSRetriever:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.doc1 = mocker.MagicMock(spec=Node)
        self.doc2 = mocker.MagicMock(spec=Node)
        self.mock_nodes = [self.doc1, self.doc2]

        self.mock_index = mocker.MagicMock()
        self.retriever = FAISSRetriever(self.mock_index)

    def test_add_docs_calls_insert_for_each_document(self):
        self.retriever.add_nodes(self.mock_nodes)

        self.mock_index.insert_nodes.assert_called()

    def test_persist(self):
        self.retriever.persist("")

        self.mock_index.storage_context.persist.assert_called()
