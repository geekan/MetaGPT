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
    mock_openai_embed_documents,
    text_embed_arr,
)


def test_ltm_search(mocker):
    mocker.patch("langchain_community.embeddings.openai.OpenAIEmbeddings.embed_documents", mock_openai_embed_documents)

    role_id = "UTUserLtm(Product Manager)"
    from metagpt.environment import Environment

    Environment
    RoleContext.model_rebuild()
    rc = RoleContext(watch={"metagpt.actions.add_requirement.UserRequirement"})
    ltm = LongTermMemory()
    ltm.recover_memory(role_id, rc)

    idea = text_embed_arr[0].get("text", "Write a cli snake game")
    message = Message(role="User", content=idea, cause_by=UserRequirement)
    news = ltm.find_news([message])
    assert len(news) == 1
    ltm.add(message)

    sim_idea = text_embed_arr[1].get("text", "Write a game of cli snake")

    sim_message = Message(role="User", content=sim_idea, cause_by=UserRequirement)
    news = ltm.find_news([sim_message])
    assert len(news) == 0
    ltm.add(sim_message)

    new_idea = text_embed_arr[2].get("text", "Write a 2048 web game")
    new_message = Message(role="User", content=new_idea, cause_by=UserRequirement)
    news = ltm.find_news([new_message])
    assert len(news) == 1
    ltm.add(new_message)

    # restore from local index
    ltm_new = LongTermMemory()
    ltm_new.recover_memory(role_id, rc)
    news = ltm_new.find_news([message])
    assert len(news) == 0

    ltm_new.recover_memory(role_id, rc)
    news = ltm_new.find_news([sim_message])
    assert len(news) == 0

    new_idea = text_embed_arr[3].get("text", "Write a Battle City")
    new_message = Message(role="User", content=new_idea, cause_by=UserRequirement)
    news = ltm_new.find_news([new_message])
    assert len(news) == 1

    ltm_new.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
