#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 10:14
@Author  : alexanderwu
@File    : test_engineer.py
"""
import pytest

from metagpt.logs import logger
from metagpt.roles.engineer import Engineer
from metagpt.utils.common import CodeParser
from tests.metagpt.roles.mock import (
    STRS_FOR_PARSING,
    TASKS,
    TASKS_TOMATO_CLOCK,
    MockMessages,
)


@pytest.mark.asyncio
async def test_engineer():
    engineer = Engineer()

    engineer.recv(MockMessages.req)
    engineer.recv(MockMessages.prd)
    engineer.recv(MockMessages.system_design)
    rsp = await engineer.handle(MockMessages.tasks)

    logger.info(rsp)
    assert "all done." == rsp.content


def test_parse_str():
    for idx, i in enumerate(STRS_FOR_PARSING):
        text = CodeParser.parse_str(f"{idx+1}", i)
        # logger.info(text)
        assert text == 'a'


def test_parse_blocks():
    tasks = CodeParser.parse_blocks(TASKS)
    logger.info(tasks.keys())
    assert 'Task list' in tasks.keys()


target_list = [
    "smart_search_engine/knowledge_base.py",
    "smart_search_engine/index.py",
    "smart_search_engine/ranking.py",
    "smart_search_engine/summary.py",
    "smart_search_engine/search.py",
    "smart_search_engine/main.py",
    "smart_search_engine/interface.py",
    "smart_search_engine/user_feedback.py",
    "smart_search_engine/security.py",
    "smart_search_engine/testing.py",
    "smart_search_engine/monitoring.py",
]


def test_parse_file_list():
    tasks = CodeParser.parse_file_list("任务列表", TASKS)
    logger.info(tasks)
    assert isinstance(tasks, list)
    assert target_list == tasks

    file_list = CodeParser.parse_file_list("Task list", TASKS_TOMATO_CLOCK, lang="python")
    logger.info(file_list)


target_code = """task_list = [
    "smart_search_engine/knowledge_base.py",
    "smart_search_engine/index.py",
    "smart_search_engine/ranking.py",
    "smart_search_engine/summary.py",
    "smart_search_engine/search.py",
    "smart_search_engine/main.py",
    "smart_search_engine/interface.py",
    "smart_search_engine/user_feedback.py",
    "smart_search_engine/security.py",
    "smart_search_engine/testing.py",
    "smart_search_engine/monitoring.py",
]
"""


def test_parse_code():
    code = CodeParser.parse_code("任务列表", TASKS, lang="python")
    logger.info(code)
    assert isinstance(code, str)
    assert target_code == code
