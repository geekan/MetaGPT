import fire

from metagpt.logs import logger
from metagpt.roles.di.team_leader import TeamLeader


async def main():
    tl = TeamLeader()
    logger.info("\n=== Adding Initial Tasks ===")
    tl.planner.plan.append_task(
        task_id="T1", dependent_task_ids=[], instruction="Create Product Requirements Document (PRD)", assignee="Alice"
    )
    tl.planner.plan.append_task(
        task_id="T2", dependent_task_ids=["T1"], instruction="Design System Architecture", assignee="Bob"
    )

    # 1. Add Development Tasks
    logger.info("\n=== Adding Development Tasks ===")
    tl.planner.plan.append_task(
        task_id="T3", dependent_task_ids=["T2"], instruction="Implement Core Function Modules", assignee="Alex"
    )

    tl.planner.plan.append_task(
        task_id="T4", dependent_task_ids=["T2"], instruction="Implement User Interface", assignee="Alex"
    )

    # 2. Complete Some Tasks
    logger.info("\n=== Execute and Complete Tasks ===")
    logger.info(f"Current Task: {tl.planner.plan.current_task.instruction}")
    tl.planner.plan.finish_current_task()  # Complete T1

    logger.info(f"Current Task: {tl.planner.plan.current_task.instruction}")
    tl.planner.plan.finish_current_task()  # Complete T2

    # 3. Replace Tasks
    logger.info("\n=== Replace Task ===")
    tl.planner.plan.replace_task(
        task_id="T3",
        new_dependent_task_ids=["T2"],
        new_instruction="Implement Core Function Modules (Add New Features)",
        new_assignee="Senior_Developer",
    )

    # 4. Add Testing Tasks
    logger.info("\n=== Add Testing Tasks ===")
    tl.planner.plan.append_task(
        task_id="T5", dependent_task_ids=["T3", "T4"], instruction="Execute Integration Tests", assignee="Edward"
    )

    # 5. Reset Task Demonstration
    logger.info("\n=== Reset Task ===")
    logger.info("Reset Task T3 (This will also reset T5 which depends on it)")
    tl.planner.plan.reset_task("T3")

    # Display Final Status
    logger.info("\n=== Final Status ===")
    logger.info(f"Completed Tasks: {len([t for t in tl.planner.plan.tasks if t.is_finished])}")
    logger.info(f"Current Task: {tl.planner.plan.current_task.instruction}")
    logger.info("All Tasks:")
    for task in tl.planner.plan.tasks:
        logger.info(f"- {task.task_id}: {task.instruction} (Completed: {task.is_finished})")


if __name__ == "__main__":
    fire.Fire(main)
