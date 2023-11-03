#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : unittest of `metagpt/memory/longterm_memory.py`
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.1 and 2.2.2 of RFC 116, change the data type of
        the `cause_by` value in the `Message` to a string to support the new message distribution feature.
"""

from metagpt.actions import BossRequirement
from metagpt.config import CONFIG
from metagpt.memory import LongTermMemory
from metagpt.roles.role import RoleContext
from metagpt.schema import Message


def test_ltm_search():
    assert hasattr(CONFIG, "long_term_memory") is True
    openai_api_key = CONFIG.openai_api_key
    assert len(openai_api_key) > 20

    role_id = "UTUserLtm(Product Manager)"
    rc = RoleContext(watch=[BossRequirement.get_class_name()])
    ltm = LongTermMemory()
    ltm.recover_memory(role_id, rc)

    idea = "Write a cli snake game"
    message = Message(role="BOSS", content=idea, cause_by=BossRequirement.get_class_name())
    news = ltm.find_news([message])
    assert len(news) == 1
    ltm.add(message)

    sim_idea = "Write a game of cli snake"
    sim_message = Message(role="BOSS", content=sim_idea, cause_by=BossRequirement.get_class_name())
    news = ltm.find_news([sim_message])
    assert len(news) == 0
    ltm.add(sim_message)

    new_idea = "Write a 2048 web game"
    new_message = Message(role="BOSS", content=new_idea, cause_by=BossRequirement.get_class_name())
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
    new_message = Message(role="BOSS", content=new_idea, cause_by=BossRequirement.get_class_name())
    news = ltm_new.find_news([new_message])
    assert len(news) == 1

    ltm_new.clear()
