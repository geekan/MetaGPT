import fire

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.logs import logger
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message


async def main():
    # Initialize the MetaGPT environment
    env = MGXEnv()
    # Add a TeamLeader role to the environment
    env.add_roles([TeamLeader()])

    # Get input from human user about what they want to do
    human_rsp = await env.ask_human("What do you want to do？")

    # Log the human response for tracking
    logger.info(human_rsp)
    # Create and publish a message with the human response in the environment
    env.publish_message(Message(content=human_rsp, role="user"))

    # Get the TeamLeader role instance named 'Mike'
    tl = env.get_role("Mike")
    # Execute the TeamLeader's tasks
    await tl.run()

    # Log information about each task in the TeamLeader's plan
    for task in tl.planner.plan.tasks:
        logger.info(f"- {task.task_id}: {task.instruction} (Completed: {task.is_finished})")

    # Send an empty response back to the human and log it
    resp = await env.reply_to_human("")
    logger.info(resp)


if __name__ == "__main__":
    fire.Fire(main)
