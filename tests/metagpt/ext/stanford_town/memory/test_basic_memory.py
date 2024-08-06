#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of BasicMemory

from datetime import datetime, timedelta

import pytest

from metagpt.ext.stanford_town.memory.agent_memory import BasicMemory
from metagpt.logs import logger

"""
memory测试思路
1. Basic Memory测试
2. Agent Memory测试
    2.1 Load & Save方法测试
    2.2 Add方法测试
    2.3 Get方法测试
"""

# Create some sample BasicMemory instances
memory1 = BasicMemory(
    memory_id="1",
    memory_count=1,
    type_count=1,
    memory_type="event",
    depth=1,
    created=datetime.now(),
    expiration=datetime.now() + timedelta(days=30),
    subject="Subject1",
    predicate="Predicate1",
    object="Object1",
    content="This is content 1",
    embedding_key="embedding_key_1",
    poignancy=1,
    keywords=["keyword1", "keyword2"],
    filling=["memory_id_2"],
)
memory2 = BasicMemory(
    memory_id="2",
    memory_count=2,
    type_count=2,
    memory_type="thought",
    depth=2,
    created=datetime.now(),
    expiration=datetime.now() + timedelta(days=30),
    subject="Subject2",
    predicate="Predicate2",
    object="Object2",
    content="This is content 2",
    embedding_key="embedding_key_2",
    poignancy=2,
    keywords=["keyword3", "keyword4"],
    filling=[],
)


@pytest.fixture
def basic_mem_set():
    basic_mem2 = memory2
    yield basic_mem2


def test_basic_mem_function(basic_mem_set):
    a, b, c = basic_mem_set.summary()
    logger.info(f"{a}{b}{c}")
    assert a == "Subject2"


def test_basic_mem_save(basic_mem_set):
    result = basic_mem_set.save_to_dict()
    logger.info(f"save结果为{result}")


if __name__ == "__main__":
    pytest.main()
