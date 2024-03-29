import pytest
from llama_index.core.schema import NodeWithScore, TextNode

from metagpt.rag.retrievers import SimpleHybridRetriever


class TestSimpleHybridRetriever:
    @pytest.fixture
    def mock_retriever(self, mocker):
        return mocker.MagicMock()

    @pytest.fixture
    def mock_hybrid_retriever(self, mock_retriever) -> SimpleHybridRetriever:
        return SimpleHybridRetriever(mock_retriever)

    @pytest.fixture
    def mock_node(self):
        return NodeWithScore(node=TextNode(id_="2"), score=0.95)

    @pytest.mark.asyncio
    async def test_aretrieve(self, mocker):
        question = "test query"

        # Create mock retrievers
        mock_retriever1 = mocker.AsyncMock()
        mock_retriever1.aretrieve.return_value = [
            NodeWithScore(node=TextNode(id_="1"), score=1.0),
            NodeWithScore(node=TextNode(id_="2"), score=0.95),
        ]

        mock_retriever2 = mocker.AsyncMock()
        mock_retriever2.aretrieve.return_value = [
            NodeWithScore(node=TextNode(id_="2"), score=0.95),
            NodeWithScore(node=TextNode(id_="3"), score=0.8),
        ]

        # Instantiate the SimpleHybridRetriever with the mock retrievers
        hybrid_retriever = SimpleHybridRetriever(mock_retriever1, mock_retriever2)

        # Call the _aretrieve method
        results = await hybrid_retriever._aretrieve(question)

        # Check if the results are as expected
        assert len(results) == 3  # Should be 3 unique nodes
        assert set(node.node.node_id for node in results) == {"1", "2", "3"}

        # Check if the scores are correct (assuming you want the highest score)
        node_scores = {node.node.node_id: node.score for node in results}
        assert node_scores["2"] == 0.95

    def test_add_nodes(self, mock_hybrid_retriever: SimpleHybridRetriever, mock_node):
        mock_hybrid_retriever.add_nodes([mock_node])
        mock_hybrid_retriever.retrievers[0].add_nodes.assert_called_once()

    def test_persist(self, mock_hybrid_retriever: SimpleHybridRetriever):
        mock_hybrid_retriever.persist("")
        mock_hybrid_retriever.retrievers[0].persist.assert_called_once()
