#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : unittest of `metagpt/memory/longterm_memory.py`
"""

from metagpt.actions import UserRequirement
from metagpt.config import CONFIG
from metagpt.memory import LongTermMemory
from metagpt.roles.role import RoleContext
from metagpt.schema import Message


def test_ltm_search():
    assert hasattr(CONFIG, "long_term_memory") is True
    openai_api_key = CONFIG.openai_api_key
    assert len(openai_api_key) > 20

    role_id = "UTUserLtm(Product Manager)"
    rc = RoleContext(watch=[UserRequirement])
    ltm = LongTermMemory()
    ltm.recover_memory(role_id, rc)

    idea = "Write a cli snake game"
    message = Message(role="User", content=idea, cause_by=UserRequirement)
    news = ltm.find_news([message])
    assert len(news) == 1
    ltm.add(message)

    sim_idea = "Write a game of cli snake"
    sim_message = Message(role="User", content=sim_idea, cause_by=UserRequirement)
    news = ltm.find_news([sim_message])
    assert len(news) == 0
    ltm.add(sim_message)

    new_idea = "Write a 2048 web game"
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

    new_idea = "Write a Battle City"
    new_message = Message(role="User", content=new_idea, cause_by=UserRequirement)
    news = ltm_new.find_news([new_message])
    assert len(news) == 1

    ltm_new.clear()
