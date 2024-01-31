import pytest

from metagpt.logs import logger
from metagpt.roles.code_interpreter import CodeInterpreter


@pytest.mark.asyncio
async def test_code_interpreter():
    requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    tools = []

    ci = CodeInterpreter(auto_run=True, use_tools=True, tools=tools)
    rsp = await ci.run(requirement)
    logger.info(rsp)
    assert len(rsp.content) > 0
