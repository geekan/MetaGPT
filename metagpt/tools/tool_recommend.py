from __future__ import annotations

import json
from typing import Any

import numpy as np
from pydantic import BaseModel, field_validator
from rank_bm25 import BM25Okapi

from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.schema import Plan
from metagpt.tools import TOOL_REGISTRY
from metagpt.tools.tool_data_type import Tool
from metagpt.tools.tool_registry import validate_tool_names
from metagpt.utils.common import CodeParser

TOOL_INFO_PROMPT = """
## Capabilities
- You can utilize pre-defined tools in any code lines from 'Available Tools' in the form of Python class or function.
- You can freely combine the use of any other public packages, like sklearn, numpy, pandas, etc..

## Available Tools:
Each tool is described in JSON format. When you call a tool, import the tool from its path first.
{tool_schemas}
"""


TOOL_RECOMMENDATION_PROMPT = """
## User Requirement:
{current_task}

## Task
Recommend up to {topk} tools from 'Available Tools' that can help solve the 'User Requirement'. 

## Available Tools:
{available_tools}

## Tool Selection and Instructions:
- Select tools most relevant to completing the 'User Requirement'.
- If you believe that no tools are suitable, indicate with an empty list.
- Only list the names of the tools, not the full schema of each tool.
- Ensure selected tools are listed in 'Available Tools'.
- Output a json list of tool names:
```json
["tool_name1", "tool_name2", ...]
```
"""


class ToolRecommender(BaseModel):
    """
    The default ToolRecommender:
    1. Recall: To be implemented in subclasses. Recall tools based on the given context and plan.
    2. Rank: Use LLM to select final candidates from recalled set.
    """

    tools: dict[str, Tool] = {}
    force: bool = False  # whether to forcedly recommend the specified tools

    @field_validator("tools", mode="before")
    @classmethod
    def validate_tools(cls, v: list[str]) -> dict[str, Tool]:
        # One can use special symbol ["<all>"] to indicate use of all registered tools
        if v == ["<all>"]:
            return TOOL_REGISTRY.get_all_tools()
        else:
            return validate_tool_names(v)

    async def recommend_tools(
        self, context: str = "", plan: Plan = None, recall_topk: int = 20, topk: int = 5
    ) -> list[Tool]:
        """
        Recommends a list of tools based on the given context and plan. The recommendation process includes two stages: recall from a large pool and rank the recalled tools to select the final set.

        Args:
            context (str): The context for tool recommendation.
            plan (Plan): The plan for tool recommendation.
            recall_topk (int): The number of tools to recall in the initial step.
            topk (int): The number of tools to return after rank as final recommendations.

        Returns:
            list[Tool]: A list of recommended tools.
        """

        if not self.tools:
            return []

        if self.force or (not context and not plan):
            # directly use what users have specified as result for forced recommendation;
            # directly use the whole set if there is no useful information
            return list(self.tools.values())

        recalled_tools = await self.recall_tools(context=context, plan=plan, topk=recall_topk)
        if not recalled_tools:
            return []

        ranked_tools = await self.rank_tools(recalled_tools=recalled_tools, context=context, plan=plan, topk=topk)

        logger.info(f"Recommended tools: \n{[tool.name for tool in ranked_tools]}")

        return ranked_tools

    async def get_recommended_tool_info(self, **kwargs) -> str:
        """
        Wrap recommended tools with their info in a string, which can be used directly in a prompt.
        """
        recommended_tools = await self.recommend_tools(**kwargs)
        if not recommended_tools:
            return ""
        tool_schemas = {tool.name: tool.schemas for tool in recommended_tools}
        return TOOL_INFO_PROMPT.format(tool_schemas=tool_schemas)

    async def recall_tools(self, context: str = "", plan: Plan = None, topk: int = 20) -> list[Tool]:
        """
        Retrieves a list of relevant tools from a large pool, based on the given context and plan.
        """
        raise NotImplementedError

    async def rank_tools(
        self, recalled_tools: list[Tool], context: str = "", plan: Plan = None, topk: int = 5
    ) -> list[Tool]:
        """
        Default rank methods for a ToolRecommender. Use LLM to rank the recalled tools based on the given context, plan, and topk value.
        """
        current_task = plan.current_task.instruction if plan else context

        available_tools = {tool.name: tool.schemas["description"] for tool in recalled_tools}
        prompt = TOOL_RECOMMENDATION_PROMPT.format(
            current_task=current_task,
            available_tools=available_tools,
            topk=topk,
        )
        rsp = await LLM().aask(prompt)
        rsp = CodeParser.parse_code(block=None, text=rsp)
        ranked_tools = json.loads(rsp)

        valid_tools = validate_tool_names(ranked_tools)

        return list(valid_tools.values())[:topk]


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
