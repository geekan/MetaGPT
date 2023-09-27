# -*- coding: utf-8 -*-
# @Date    : 2023/09/28 00:03
# @Author  : yuymf
# @Desc    :
import asyncio
from metagpt.logs import logger
from metagpt.minecraft_team import GameEnvironment


async def main():
    test_code = "bot.chat(`/time set ${getNextTime()}`);"
    mc_port = 2745
    ge = GameEnvironment()
    ge.set_mc_port(mc_port)
    ge.update_code(test_code)
    result = await ge.on_event()
    logger.info("On event test done")


if __name__ == "__main__":
    asyncio.run(main())
