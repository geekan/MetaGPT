#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of `metagpt/memory/longterm_memory.py`

from metagpt.config import CONFIG
from metagpt.schema import Message
from metagpt.actions import BossRequirement
from metagpt.roles.role import RoleContext
from metagpt.memory import LongTermMemory


def test_ltm_search():
    assert hasattr(CONFIG, "long_term_memory") is True
    openai_api_key = CONFIG.openai_api_key
    assert len(openai_api_key) > 20

    role_id = 'UTUserLtm(Product Manager)'
    rc = RoleContext(watch=[BossRequirement])
    ltm = LongTermMemory()
    ltm.recover_memory(role_id, rc)

    idea = 'Write a cli snake game'
    message = Message(role='BOSS', content=idea, cause_by=BossRequirement)
    news = ltm.find_news([message])
    assert len(news) == 1
    ltm.add(message)

    sim_idea = 'Write a game of cli snake'
    sim_message = Message(role='BOSS', content=sim_idea, cause_by=BossRequirement)
    news = ltm.find_news([sim_message])
    assert len(news) == 0
    ltm.add(sim_message)

    new_idea = 'Write a 2048 web game'
    new_message = Message(role='BOSS', content=new_idea, cause_by=BossRequirement)
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

    new_idea = 'Write a Battle City'
    new_message = Message(role='BOSS', content=new_idea, cause_by=BossRequirement)
    news = ltm_new.find_news([new_message])
    assert len(news) == 1

    ltm_new.clear()
