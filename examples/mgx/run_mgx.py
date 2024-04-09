# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import asyncio

from metagpt.roles.di.mgx import MGX

requirement = (
    # "design a game using Gym (an open source Python library), including a graphical interface and interactive gameplay"
    # "帮我把pip的源设置成：https://pypi.tuna.tsinghua.edu.cn/simple"
    # "This is a website url does not require login: https://demosc.chinaz.net/Files/DownLoad//moban/202404/moban7767 please write a similar web page,developed in vue language, The package.json dependency must be generated"
    # "I would like to imitate the website available at https://demosc.chinaz.net/Files/DownLoad//moban/202404/moban7767. Could you please browse through it?"
    "Create a 2048 Game"
)


async def main(requirement: str = ""):
    mgx = MGX(use_intent=True, tools=["software development"])
    await mgx.run(requirement)


if __name__ == "__main__":
    asyncio.run(main(requirement))
