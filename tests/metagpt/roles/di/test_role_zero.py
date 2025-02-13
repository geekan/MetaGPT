import pytest

from metagpt.actions import UserRequirement
from metagpt.logs import logger
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_model_validators():
    """Test all model validators"""
    role = RoleZero()
    # Test set_plan_and_tool
    assert role.react_mode == "react"
    assert role.planner is not None

    # Test set_tool_execution
    assert "Plan.append_task" in role.tool_execution_map
    assert "RoleZero.ask_human" in role.tool_execution_map

    # Test set_longterm_memory
    assert role.rc.memory is not None


@pytest.mark.asyncio
async def test_think_react_cycle():
    """Test the think-react cycle"""
    # Setup test conditions
    role = RoleZero(tools=["Plan"])
    role.rc.todo = True
    role.planner.plan.goal = "Test goal"
    role.respond_language = "English"

    # Test _think
    result = await role._think()
    assert result is True

    role.rc.news = [Message(content="Test", cause_by=UserRequirement())]
    result = await role._react()
    logger.info(result)
    assert isinstance(result, Message)
