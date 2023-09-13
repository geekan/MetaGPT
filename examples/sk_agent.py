#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:36
@Author  : femto Zheng
@File    : sk_agent.py
"""
import asyncio

from metagpt.actions import BossRequirement
from metagpt.roles.sk_agent import SkAgent
from metagpt.schema import Message


async def main():
    task = """
    Tomorrow is Valentine's day. I need to come up with a few date ideas. She speaks French so write it in French.
    Convert the text to uppercase"""
    role = SkAgent()
    await role.run(Message(content=task, cause_by=BossRequirement))

    # from semantic_kernel.planning import SequentialPlanner
    # role.planner = SequentialPlanner(role.kernel)
    # await role.run(Message(content=task, cause_by=BossRequirement))
    # %%


if __name__ == "__main__":
    asyncio.run(main())
