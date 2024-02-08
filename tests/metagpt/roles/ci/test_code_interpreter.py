import pytest

from metagpt.logs import logger
from metagpt.roles.ci.code_interpreter import CodeInterpreter


@pytest.mark.asyncio
@pytest.mark.parametrize("auto_run", [(True), (False)])
async def test_code_interpreter(mocker, auto_run):
    mocker.patch("metagpt.actions.ci.execute_nb_code.ExecuteNbCode.run", return_value=("a successful run", True))
    mocker.patch("builtins.input", return_value="confirm")

    requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    tools = []

    ci = CodeInterpreter(auto_run=auto_run, use_tools=True, tools=tools)
    rsp = await ci.run(requirement)
    logger.info(rsp)
    assert len(rsp.content) > 0

    finished_tasks = ci.planner.plan.get_finished_tasks()
    assert len(finished_tasks) > 0
    assert len(finished_tasks[0].code) > 0  # check one task to see if code is recorded
