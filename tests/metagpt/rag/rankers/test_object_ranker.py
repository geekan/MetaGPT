import json

import pytest
from llama_index.core.schema import NodeWithScore, QueryBundle
from pydantic import BaseModel

from metagpt.rag.rankers.object_ranker import ObjectSortPostprocessor
from metagpt.rag.schema import ObjectNode


class Record(BaseModel):
    score: int


class TestObjectSortPostprocessor:
    @pytest.fixture
    def mock_nodes_with_scores(self):
        nodes = [
            NodeWithScore(node=ObjectNode(metadata={"obj_json": Record(score=10).model_dump_json()}), score=10),
            NodeWithScore(node=ObjectNode(metadata={"obj_json": Record(score=20).model_dump_json()}), score=20),
            NodeWithScore(node=ObjectNode(metadata={"obj_json": Record(score=5).model_dump_json()}), score=5),
        ]
        return nodes

    @pytest.fixture
    def mock_query_bundle(self, mocker):
        return mocker.MagicMock(spec=QueryBundle)

    def test_sort_descending(self, mock_nodes_with_scores, mock_query_bundle):
        postprocessor = ObjectSortPostprocessor(field_name="score", order="desc")
        sorted_nodes = postprocessor._postprocess_nodes(mock_nodes_with_scores, mock_query_bundle)
        assert [node.score for node in sorted_nodes] == [20, 10, 5]

    def test_sort_ascending(self, mock_nodes_with_scores, mock_query_bundle):
        postprocessor = ObjectSortPostprocessor(field_name="score", order="asc")
        sorted_nodes = postprocessor._postprocess_nodes(mock_nodes_with_scores, mock_query_bundle)
        assert [node.score for node in sorted_nodes] == [5, 10, 20]

    def test_top_n_limit(self, mock_nodes_with_scores, mock_query_bundle):
        postprocessor = ObjectSortPostprocessor(field_name="score", order="desc", top_n=2)
        sorted_nodes = postprocessor._postprocess_nodes(mock_nodes_with_scores, mock_query_bundle)
        assert len(sorted_nodes) == 2
        assert [node.score for node in sorted_nodes] == [20, 10]

    def test_invalid_json_metadata(self, mock_query_bundle):
        nodes = [NodeWithScore(node=ObjectNode(metadata={"obj_json": "invalid_json"}), score=10)]
        postprocessor = ObjectSortPostprocessor(field_name="score", order="desc")
        with pytest.raises(ValueError):
            postprocessor._postprocess_nodes(nodes, mock_query_bundle)

    def test_missing_query_bundle(self, mock_nodes_with_scores):
        postprocessor = ObjectSortPostprocessor(field_name="score", order="desc")
        with pytest.raises(ValueError):
            postprocessor._postprocess_nodes(mock_nodes_with_scores, query_bundle=None)

    def test_field_not_found_in_object(self, mock_query_bundle):
        nodes = [NodeWithScore(node=ObjectNode(metadata={"obj_json": json.dumps({"not_score": 10})}), score=10)]
        postprocessor = ObjectSortPostprocessor(field_name="score", order="desc")
        with pytest.raises(ValueError):
            postprocessor._postprocess_nodes(nodes, query_bundle=mock_query_bundle)

    def test_not_nodes(self, mock_query_bundle):
        nodes = []
        postprocessor = ObjectSortPostprocessor(field_name="score", order="desc")
        result = postprocessor._postprocess_nodes(nodes, mock_query_bundle)
        assert result == []

    def test_class_name(self):
        assert ObjectSortPostprocessor.class_name() == "ObjectSortPostprocessor"
