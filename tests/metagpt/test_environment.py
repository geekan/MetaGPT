#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:47
@Author  : alexanderwu
@File    : test_environment.py
"""

from pathlib import Path

import pytest

from metagpt.actions import UserRequirement
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
    Role,
)
from metagpt.schema import Message, UserMessage
from metagpt.utils.common import any_to_str, is_send_to

serdeser_path = Path(__file__).absolute().parent.joinpath("../data/serdeser_storage")


class MockEnv(Environment):
    def publish_message(self, message: Message, peekable: bool = True) -> bool:
        logger.info(f"{message.metadata}:{message.content}")
        consumers = []
        for role, addrs in self.member_addrs.items():
            if is_send_to(message, addrs):
                role.put_message(message)
                consumers.append(role)
        if not consumers:
            logger.warning(f"Message no recipients: {message.dump()}")
        if message.cause_by in [any_to_str(UserRequirement), any_to_str(PrepareDocuments)]:
            assert len(consumers) == 1

        return True


@pytest.fixture
def env():
    context = Context()
    context.kwargs.tag = __file__
    return MockEnv(context=context)


def test_add_role(env: Environment):
    role = ProductManager(
        name="Alice", profile="product manager", goal="create a new product", constraints="limited resources"
    )
    env.add_role(role)
    assert env.get_role(str(role._setting)) == role


def test_get_roles(env: Environment):
    role1 = Role(name="Alice", profile="product manager", goal="create a new product", constraints="limited resources")
    role2 = Role(name="Bob", profile="engineer", goal="develop the new product", constraints="short deadline")
    env.add_role(role1)
    env.add_role(role2)
    roles = env.get_roles()
    assert roles == {role1.profile: role1, role2.profile: role2}


@pytest.mark.asyncio
async def test_publish_and_process_message(env: Environment):
    if env.context.git_repo:
        env.context.git_repo.delete_repository()
        env.context.git_repo = None

    product_manager = ProductManager(name="Alice", profile="Product Manager", goal="做AI Native产品", constraints="资源有限")
    architect = Architect(
        name="Bob", profile="Architect", goal="设计一个可用、高效、较低成本的系统，包括数据结构与接口", constraints="资源有限，需要节省成本"
    )

    env.add_roles([product_manager, architect])

    env.publish_message(UserMessage(content="需要一个基于LLM做总结的搜索引擎", cause_by=UserRequirement, send_to=product_manager))
    await env.run(k=2)
    logger.info(f"{env.history}")
    assert len(env.history.storage) == 0


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "send_to"),
    [
        ("snake game", any_to_str(ProductManager)),
        (
            "Rewrite the PRD file of the project at '/Users/iorishinier/github/MetaGPT/workspace/snake_game', add 'moving enemy' to the original requirement",
            any_to_str(ProductManager),
        ),
        (
            "Add 'random moving enemy, and dispears after 10 seconds' design to the project at '/Users/iorishinier/github/MetaGPT/workspace/snake_game'",
            any_to_str(Architect),
        ),
        (
            'Rewrite the tasks file of the project at "/Users/iorishinier/github/MetaGPT/workspace/snake_game"',
            any_to_str(ProjectManager),
        ),
        (
            "src filename  is 'game.py', Uncaught SyntaxError: Identifier 'Position' has already been declared (at game.js:1:1), the project at '/Users/iorishinier/github/bak/MetaGPT/workspace/snake_game'",
            any_to_str(Engineer),
        ),
        (
            "Rewrite the unit test of 'main.py' at '/Users/iorishinier/github/MetaGPT/workspace/snake_game'",
            any_to_str(QaEngineer),
        ),
    ],
)
async def test_env(content, send_to):
    context = Context()
    env = MockEnv(context=context)
    env.add_roles(
        [
            ProductManager(context=context),
            Architect(context=context),
            ProjectManager(context=context),
            Engineer(n_borg=5, use_code_review=True, context=context),
            QaEngineer(context=context, test_round_allowed=2),
        ]
    )
    msg = UserMessage(content=content, send_to=send_to)
    env.publish_message(msg)
    while not env.is_idle:
        await env.run()
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
