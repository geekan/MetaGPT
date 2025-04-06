from __future__ import annotations

from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from metagpt.core.logs import logger
from metagpt.core.schema import Plan
from metagpt.core.tools import TOOL_REGISTRY
from metagpt.core.tools.base import Tool
from metagpt.core.tools.tool_recommend_base import ToolRecommender


class TypeMatchToolRecommender(ToolRecommender):
    """
    A legacy ToolRecommender using task type matching at the recall stage:
    1. Recall: Find tools based on exact match between task type and tool tag;
    2. Rank: LLM rank, the same as the default ToolRecommender.
    """

    async def recall_tools(self, context: str = "", plan: Plan = None, topk: int = 20) -> list[Tool]:
        if not plan:
            return list(self.tools.values())[:topk]

        # find tools based on exact match between task type and tool tag
        task_type = plan.current_task.task_type
        candidate_tools = TOOL_REGISTRY.get_tools_by_tag(task_type)
        candidate_tool_names = set(self.tools.keys()) & candidate_tools.keys()
        recalled_tools = [candidate_tools[tool_name] for tool_name in candidate_tool_names][:topk]

        logger.info(f"Recalled tools: \n{[tool.name for tool in recalled_tools]}")

        return recalled_tools


class BM25ToolRecommender(ToolRecommender):
    """
    A ToolRecommender using BM25 at the recall stage:
    1. Recall: Querying tool descriptions with task instruction if plan exists. Otherwise, return all user-specified tools;
    2. Rank: LLM rank, the same as the default ToolRecommender.
    """

    bm25: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_corpus()

    def _init_corpus(self):
        corpus = [f"{tool.name} {tool.tags}: {tool.schemas['description']}" for tool in self.tools.values()]
        tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def _tokenize(self, text):
        return text.split()  # FIXME: needs more sophisticated tokenization

    async def recall_tools(self, context: str = "", plan: Plan = None, topk: int = 20) -> list[Tool]:
        query = plan.current_task.instruction if plan else context

        query_tokens = self._tokenize(query)
        doc_scores = self.bm25.get_scores(query_tokens)
        top_indexes = np.argsort(doc_scores)[::-1][:topk]
        recalled_tools = [list(self.tools.values())[index] for index in top_indexes]

        logger.info(
            f"Recalled tools: \n{[tool.name for tool in recalled_tools]}; Scores: {[np.round(doc_scores[index], 4) for index in top_indexes]}"
        )

        return recalled_tools


class EmbeddingToolRecommender(ToolRecommender):
    """
    NOTE: To be implemented.
    A ToolRecommender using embeddings at the recall stage:
    1. Recall: Use embeddings to calculate the similarity between query and tool info;
    2. Rank: LLM rank, the same as the default ToolRecommender.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def recall_tools(self, context: str = "", plan: Plan = None, topk: int = 20) -> list[Tool]:
        pass
