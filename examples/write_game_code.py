import asyncio

from metagpt.logs import logger
from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.schema import Message
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.roles.di.engineer2 import Engineer2


async def main():
    msg = "Write code for a 2048 game"
    env = MGXEnv()
    env.add_roles([TeamLeader(), Engineer2()])
    env.publish_message(Message(content=msg, role="user"))
    tl = env.get_role("Mike")
    await tl.run()

    role = env.get_role("Alex")
    result = await role.run(msg)
    logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
