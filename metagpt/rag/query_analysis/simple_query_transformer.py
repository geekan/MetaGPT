from typing import Optional

from llama_index.core.callbacks import CallbackManager
from llama_index.core.indices.query.query_transform.base import BaseQueryTransform
from llama_index.core.query_engine import TransformQueryEngine

from metagpt.rag.engines.simple import SimpleEngine


class SimpleQueryTransformer(TransformQueryEngine):
    """Simple query engine

    Extends the TransformQueryEngine to handle simpler queries using a basic query engine.

    Args:
        query_engine (BaseQueryEngine): A simple query engine object.
        query_transform (BaseQueryTransform): A query transform object.
        transform_metadata (Optional[dict]): metadata to pass to the query transform.
        callback_manager (Optional[CallbackManager]): A callback manager.
    """

    def __init__(
        self,
        query_engine: SimpleEngine,
        query_transform: BaseQueryTransform,
        transform_metadata: Optional[dict] = None,
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        super().__init__(
            query_engine=query_engine,
            query_transform=query_transform,
            transform_metadata=transform_metadata,
            callback_manager=callback_manager,
        )
