import pytest
from tqdm import tqdm

from metagpt.logs import logger
from metagpt.roles.ml_engineer import ExecutePyCode, MLEngineer
from metagpt.schema import Plan


def reset(role):
    """Restart role with the same goal."""
    role.working_memory.clear()
    role.planner.plan = Plan(goal=role.planner.plan.goal)
    role.execute_code = ExecutePyCode()


async def make_use_tools(requirement: str, auto_run: bool = True):
    """make and use tools for requirement."""
    role = MLEngineer(goal=requirement, auto_run=auto_run)
    # make udfs
    role.use_tools = False
    role.use_code_steps = False
    role.make_udfs = True
    role.use_udfs = False
    await role.run(requirement)
    # use udfs
    reset(role)
    role.make_udfs = False
    role.use_udfs = True
    role.use_code_steps = False
    role.use_tools = False
    await role.run(requirement)


@pytest.mark.asyncio
async def test_make_use_tools():
    requirements = [
        "Run data analysis on sklearn Iris dataset, include a plot",
        "Run data analysis on sklearn Diabetes dataset, include a plot",
        "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy",
        "Run data analysis on sklearn Wisconsin Breast Cancer dataset, include a plot, train a model to predict targets (20% as validation), and show validation accuracy",
        "Run EDA and visualization on this dataset, train a model to predict survival, report metrics on validation set (20%), dataset: tests/data/titanic.csv",
    ]
    success = 0
    for requirement in tqdm(requirements, total=len(requirements)):
        try:
            await make_use_tools(requirement)
            success += 1
        except Exception as e:
            logger.error(f"Found Error in {requirement}, {e}")
    logger.info(f"success: {round(success/len(requirements), 1)*100}%")
