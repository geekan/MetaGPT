# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import asyncio

from metagpt.roles.di.mgx import MGX

requirement = (
    # "design a game using Gym (an open source Python library), including a graphical interface and interactive gameplay"
    'Create a "2048 game"'
)


async def main(requirement: str = ""):
    mgx = MGX(use_intent=True)
    await mgx.run(requirement)


if __name__ == "__main__":
    asyncio.run(main(requirement))
