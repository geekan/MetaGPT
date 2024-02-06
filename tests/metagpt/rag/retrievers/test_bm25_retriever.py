import pytest
from llama_index.schema import Node

from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever


class TestDynamicBM25Retriever:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        # 创建模拟的Document对象
        self.doc1 = mocker.MagicMock(spec=Node)
        self.doc1.get_content.return_value = "Document content 1"
        self.doc2 = mocker.MagicMock(spec=Node)
        self.doc2.get_content.return_value = "Document content 2"
        self.mock_nodes = [self.doc1, self.doc2]

        # 模拟nodes和tokenizer参数
        mock_nodes = []
        mock_tokenizer = mocker.MagicMock()
        self.mock_bm25okapi = mocker.patch("rank_bm25.BM25Okapi")

        # 初始化DynamicBM25Retriever对象，并提供必需的参数
        self.retriever = DynamicBM25Retriever(nodes=mock_nodes, tokenizer=mock_tokenizer)

    def test_add_docs_updates_nodes_and_corpus(self):
        # Execute
        self.retriever.add_nodes(self.mock_nodes)

        # Assertions
        assert len(self.retriever._nodes) == len(self.mock_nodes)
        assert len(self.retriever._corpus) == len(self.mock_nodes)
        self.retriever._tokenizer.assert_called()
        self.mock_bm25okapi.assert_called()
