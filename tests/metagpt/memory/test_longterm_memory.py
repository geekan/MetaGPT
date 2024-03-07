#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : unittest of `metagpt/memory/longterm_memory.py`
"""


import pytest

from metagpt.actions import UserRequirement
from metagpt.memory.longterm_memory import LongTermMemory
from metagpt.roles.role import RoleContext
from metagpt.schema import Message
from tests.metagpt.memory.mock_text_embed import (
    mock_openai_aembed_document,
    mock_openai_embed_document,
    mock_openai_embed_documents,
    text_embed_arr,
)


@pytest.mark.asyncio
async def test_ltm_search(mocker):
    mocker.patch("llama_index.embeddings.openai.base.OpenAIEmbedding._get_text_embeddings", mock_openai_embed_documents)
    mocker.patch("llama_index.embeddings.openai.base.OpenAIEmbedding._get_text_embedding", mock_openai_embed_document)
    mocker.patch(
        "llama_index.embeddings.openai.base.OpenAIEmbedding._aget_query_embedding", mock_openai_aembed_document
    )

    role_id = "UTUserLtm(Product Manager)"
    from metagpt.environment import Environment

    Environment
    RoleContext.model_rebuild()
    rc = RoleContext(watch={"metagpt.actions.add_requirement.UserRequirement"})
    ltm = LongTermMemory()
    ltm.recover_memory(role_id, rc)

    idea = text_embed_arr[0].get("text", "Write a cli snake game")
    message = Message(role="User", content=idea, cause_by=UserRequirement)
    news = await ltm.find_news([message])
    assert len(news) == 1
    ltm.add(message)

    sim_idea = text_embed_arr[1].get("text", "Write a game of cli snake")

    sim_message = Message(role="User", content=sim_idea, cause_by=UserRequirement)
    news = await ltm.find_news([sim_message])
    assert len(news) == 0
    ltm.add(sim_message)

    new_idea = text_embed_arr[2].get("text", "Write a 2048 web game")
    new_message = Message(role="User", content=new_idea, cause_by=UserRequirement)
    news = await ltm.find_news([new_message])
    assert len(news) == 1
    ltm.add(new_message)

    ltm.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
