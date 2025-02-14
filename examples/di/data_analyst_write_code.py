import fire

from metagpt.logs import logger
from metagpt.roles.di.data_analyst import DataAnalyst


async def main():
    # Create an instance of DataAnalyst role
    analyst = DataAnalyst()

    # Set the main goal for the planner - constructing a 2D array
    analyst.planner.plan.goal = "construct a two-dimensional array"

    # Add a specific task to the planner with detailed parameters:
    # - task_id: Unique identifier for the task
    # - dependent_task_ids: List of tasks that need to be completed before this one (empty in this case)
    # - instruction: Description of what needs to be done
    # - assignee: Who will execute the task (David)
    # - task_type: Category of the task (DATA_ANALYSIS)
    analyst.planner.plan.append_task(
        task_id="1",
        dependent_task_ids=[],
        instruction="construct a two-dimensional array",
        assignee="David",
        task_type="DATA_ANALYSIS",
    )

    # Execute the code generation and execution for creating a 2D array
    # The write_and_exec_code method will:
    # 1. Generate the necessary code for creating a 2D array
    # 2. Execute the generated code
    # 3. Return the result
    result = await analyst.write_and_exec_code("construct a two-dimensional array")

    # Log the result of the code execution
    logger.info(result)


if __name__ == "__main__":
    fire.Fire(main)
