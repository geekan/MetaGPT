import fire

from metagpt.logs import logger
from metagpt.roles.di.team_leader import TeamLeader


async def main():
    # Create an instance of TeamLeader
    tl = TeamLeader()

    # Update the plan with the goal to create a 2048 game
    # This will auto generate tasks needed to accomplish the goal
    await tl.planner.update_plan(goal="create a 2048 game.")

    # Iterate through all tasks in the plan
    # Log each task's ID, instruction and completion status
    for task in tl.planner.plan.tasks:
        logger.info(f"- {task.task_id}: {task.instruction} (Completed: {task.is_finished})")


if __name__ == "__main__":
    fire.Fire(main)
