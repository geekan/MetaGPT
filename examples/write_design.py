import asyncio

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.logs import logger
from metagpt.roles.architect import Architect
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message


async def main():
    msg = "Write a TRD for a snake game"
    env = MGXEnv()
    env.add_roles([TeamLeader(), Architect()])
    env.publish_message(Message(content=msg, role="user"))
    tl = env.get_role("Mike")
    await tl.run()

    role = env.get_role("Bob")
    result = await role.run(msg)
    logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
