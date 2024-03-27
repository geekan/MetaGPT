import pytest

from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter


@pytest.mark.asyncio
@pytest.mark.parametrize("auto_run", [(True), (False)])
async def test_interpreter(mocker, auto_run):
    mocker.patch("metagpt.actions.di.execute_nb_code.ExecuteNbCode.run", return_value=("a successful run", True))
    mocker.patch("builtins.input", return_value="confirm")

    requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."

    di = DataInterpreter(auto_run=auto_run)
    rsp = await di.run(requirement)
    logger.info(rsp)
    assert len(rsp.content) > 0

    finished_tasks = di.planner.plan.get_finished_tasks()
    assert len(finished_tasks) > 0
    assert len(finished_tasks[0].code) > 0  # check one task to see if code is recorded


@pytest.mark.asyncio
async def test_interpreter_react_mode(mocker):
    mocker.patch("metagpt.actions.di.execute_nb_code.ExecuteNbCode.run", return_value=("a successful run", True))

    requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."

    di = DataInterpreter(react_mode="react")
    rsp = await di.run(requirement)
    logger.info(rsp)
    assert len(rsp.content) > 0
