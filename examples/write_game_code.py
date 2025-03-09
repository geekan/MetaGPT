import asyncio
import time

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.roles.di.engineer2 import Engineer2
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message


async def main(requirement="", user_defined_recipient="", enable_human_input=False, allow_idle_time=30):
    env = MGXEnv()
    env.add_roles([TeamLeader(), Engineer2()])

    msg = Message(content=requirement)
    env.attach_images(msg)  # attach image content if applicable

    if user_defined_recipient:
        msg.send_to = {user_defined_recipient}
        env.publish_message(msg, user_defined_recipient=user_defined_recipient)
    else:
        env.publish_message(msg)

    allow_idle_time = allow_idle_time if enable_human_input else 1
    start_time = time.time()
    while time.time() - start_time < allow_idle_time:
        if not env.is_idle:
            await env.run()
            start_time = time.time()  # reset start time


if __name__ == "__main__":
    requirement = "Write code for a 2048 game"
    user_defined_recipient = ""

    asyncio.run(
        main(
            requirement=requirement,
            user_defined_recipient=user_defined_recipient,
            enable_human_input=False,
            allow_idle_time=60,
        )
    )
