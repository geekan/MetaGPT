import pytest
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

from metagpt.rag.rankers.base import RAGRanker


class SimpleRAGRanker(RAGRanker):
    def _postprocess_nodes(self, nodes, query_bundle=None):
        return [NodeWithScore(node=node.node, score=node.score + 1) for node in nodes]


class TestSimpleRAGRanker:
    @pytest.fixture
    def ranker(self):
        return SimpleRAGRanker()

    def test_postprocess_nodes_increases_scores(self, ranker):
        nodes = [NodeWithScore(node=TextNode(text="a"), score=10), NodeWithScore(node=TextNode(text="b"), score=20)]
        query_bundle = QueryBundle(query_str="test query")

        processed_nodes = ranker._postprocess_nodes(nodes, query_bundle)

        assert all(node.score == original_node.score + 1 for node, original_node in zip(processed_nodes, nodes))
