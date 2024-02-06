import pytest
from llama_index.schema import Node

from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever


class TestFAISSRetriever:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        # 创建模拟的Document对象
        self.doc1 = mocker.MagicMock(spec=Node)
        self.doc2 = mocker.MagicMock(spec=Node)
        self.mock_nodes = [self.doc1, self.doc2]

        # 模拟FAISSRetriever的_index属性
        self.mock_index = mocker.MagicMock()
        self.retriever = FAISSRetriever(self.mock_index)

    def test_add_docs_calls_insert_for_each_document(self, mocker):
        self.retriever.add_nodes(self.mock_nodes)

        assert self.mock_index.insert_nodes.assert_called
