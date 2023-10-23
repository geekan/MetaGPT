#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:47
@Author  : alexanderwu
@File    : test_environment.py
"""

import pytest

from metagpt.actions import BossRequirement
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.manager import Manager
from metagpt.roles import Architect, ProductManager, Role
from metagpt.schema import Message


@pytest.fixture
def env():
    return Environment()


def test_add_role(env: Environment):
    role = ProductManager("Alice", "product manager", "create a new product", "limited resources")
    env.add_role(role)
    assert env.get_role(role.profile) == role


def test_get_roles(env: Environment):
    role1 = Role("Alice", "product manager", "create a new product", "limited resources")
    role2 = Role("Bob", "engineer", "develop the new product", "short deadline")
    env.add_role(role1)
    env.add_role(role2)
    roles = env.get_roles()
    assert roles == {role1.profile: role1, role2.profile: role2}


def test_set_manager(env: Environment):
    manager = Manager()
    env.set_manager(manager)
    assert env.manager == manager


@pytest.mark.asyncio
async def test_publish_and_process_message(env: Environment):
    product_manager = ProductManager("Alice", "Product Manager", "做AI Native产品", "资源有限")
    architect = Architect("Bob", "Architect", "设计一个可用、高效、较低成本的系统，包括数据结构与接口", "资源有限，需要节省成本")

    env.add_roles([product_manager, architect])
    env.set_manager(Manager())
    env.publish_message(Message(role="BOSS", content="需要一个基于LLM做总结的搜索引擎", cause_by=BossRequirement))

    await env.run(k=2)
    logger.info(f"{env.history=}")
    assert len(env.history) > 10
