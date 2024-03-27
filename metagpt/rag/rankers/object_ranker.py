"""Object ranker."""

import heapq
import json
from typing import Literal, Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from pydantic import Field

from metagpt.rag.schema import ObjectNode


class ObjectSortPostprocessor(BaseNodePostprocessor):
    """Sorted by object's field, desc or asc.

    Assumes nodes is list of ObjectNode with score.
    """

    field_name: str = Field(..., description="field name of the object, field's value must can be compared.")
    order: Literal["desc", "asc"] = Field(default="desc", description="the direction of order.")
    top_n: int = 5

    @classmethod
    def class_name(cls) -> str:
        return "ObjectSortPostprocessor"

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> list[NodeWithScore]:
        """Postprocess nodes."""
        if query_bundle is None:
            raise ValueError("Missing query bundle in extra info.")

        if not nodes:
            return []

        self._check_metadata(nodes[0].node)

        sort_key = lambda node: json.loads(node.node.metadata["obj_json"])[self.field_name]
        return self._get_sort_func()(self.top_n, nodes, key=sort_key)

    def _check_metadata(self, node: ObjectNode):
        try:
            obj_dict = json.loads(node.metadata.get("obj_json"))
        except Exception as e:
            raise ValueError(f"Invalid object json in metadata: {node.metadata}, error: {e}")

        if self.field_name not in obj_dict:
            raise ValueError(f"Field '{self.field_name}' not found in object: {obj_dict}")

    def _get_sort_func(self):
        return heapq.nlargest if self.order == "desc" else heapq.nsmallest
