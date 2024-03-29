#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of AgentMemory

from datetime import datetime, timedelta

import pytest

from metagpt.ext.stanford_town.memory.agent_memory import AgentMemory
from metagpt.ext.stanford_town.memory.retrieve import agent_retrieve
from metagpt.ext.stanford_town.utils.const import STORAGE_PATH
from metagpt.logs import logger

"""
memory测试思路
1. Basic Memory测试
2. Agent Memory测试
    2.1 Load & Save方法测试; Load方法中使用了add方法，验证Load即可验证所有add
    2.2 Get方法测试
"""
memory_easy_storage_path = STORAGE_PATH.joinpath(
    "base_the_ville_isabella_maria_klaus/personas/Isabella Rodriguez/bootstrap_memory/associative_memory",
)
memroy_chat_storage_path = STORAGE_PATH.joinpath(
    "base_the_ville_isabella_maria_klaus/personas/Isabella Rodriguez/bootstrap_memory/associative_memory",
)
memory_save_easy_test_path = STORAGE_PATH.joinpath(
    "base_the_ville_isabella_maria_klaus/personas/Isabella Rodriguez/bootstrap_memory/test_memory",
)
memory_save_chat_test_path = STORAGE_PATH.joinpath(
    "base_the_ville_isabella_maria_klaus/personas/Isabella Rodriguez/bootstrap_memory/test_memory",
)


class TestAgentMemory:
    @pytest.fixture
    def agent_memory(self):
        # 创建一个AgentMemory实例并返回，可以在所有测试用例中共享
        test_agent_memory = AgentMemory()
        test_agent_memory.set_mem_path(memroy_chat_storage_path)
        return test_agent_memory

    def test_load(self, agent_memory):
        logger.info(f"存储路径为：{agent_memory.memory_saved}")
        logger.info(f"存储记忆条数为：{len(agent_memory.storage)}")
        logger.info(f"kw_strength为{agent_memory.kw_strength_event},{agent_memory.kw_strength_thought}")
        logger.info(f"embeeding.json条数为{len(agent_memory.embeddings)}")

        assert agent_memory.embeddings is not None

    def test_save(self, agent_memory):
        try:
            agent_memory.save(memory_save_chat_test_path)
            logger.info("成功存储")
        except:
            pass

    def test_summary_function(self, agent_memory):
        logger.info(f"event长度为{len(agent_memory.event_list)}")
        logger.info(f"thought长度为{len(agent_memory.thought_list)}")
        logger.info(f"chat长度为{len(agent_memory.chat_list)}")
        result1 = agent_memory.get_summarized_latest_events(4)
        logger.info(f"总结最近事件结果为:{result1}")

    def test_get_last_chat_function(self, agent_memory):
        result2 = agent_memory.get_last_chat("customers")
        logger.info(f"上一次对话是{result2}")

    def test_retrieve_function(self, agent_memory):
        focus_points = ["who i love?"]
        retrieved = dict()
        for focal_pt in focus_points:
            nodes = [
                [i.last_accessed, i]
                for i in agent_memory.event_list + agent_memory.thought_list
                if "idle" not in i.embedding_key
            ]
            nodes = sorted(nodes, key=lambda x: x[0])
            nodes = [i for created, i in nodes]
            results = agent_retrieve(agent_memory, datetime.now() - timedelta(days=120), 0.99, focal_pt, nodes, 5)
            final_result = []
            for n in results:
                for i in agent_memory.storage:
                    if i.memory_id == n:
                        i.last_accessed = datetime.now() - timedelta(days=120)
                        final_result.append(i)

            retrieved[focal_pt] = final_result
        logger.info(f"检索结果为{retrieved}")
