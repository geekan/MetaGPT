import json
import pytest
from unittest.mock import AsyncMock, patch

from metagpt.roles.di.swe_agent import SWEAgent
from metagpt.schema import Message
from metagpt.tools.libs.terminal import Bash


@pytest.fixture
def mock_terminal():
    terminal = AsyncMock(spec=Bash)
    terminal.run = AsyncMock()
    return terminal


@pytest.fixture
def mock_extract_patch():
    with patch('metagpt.tools.swe_agent_commands.swe_agent_utils.extract_patch') as mock:
        mock.return_value = 'test_patch'
        yield mock


@pytest.fixture
def swe_agent(mock_terminal):
    agent = SWEAgent()
    agent.terminal = mock_terminal
    # Mock super()._think and super()._act
    agent._think = AsyncMock(return_value=True)
    agent._act = AsyncMock(return_value=Message(content='test'))
    return agent


@pytest.mark.asyncio
async def test_initialization():
    """Test SWEAgent initialization and attributes"""
    agent = SWEAgent()
    assert agent.name == 'Swen'
    assert agent.profile == 'Issue Solver'
    assert isinstance(agent.terminal, Bash)
    assert agent.output_diff == ''
    assert agent.max_react_loop == 40
    assert agent.run_eval is False


@pytest.mark.asyncio
async def test_think(swe_agent):
    """Test _think method with mocked dependencies"""
    # Mock _format_instruction
    swe_agent._format_instruction = AsyncMock()

    result = await swe_agent._think()
    assert result is True
    swe_agent._format_instruction.assert_called_once()


@pytest.mark.asyncio
async def test_format_instruction(swe_agent):
    """Test _format_instruction with mocked terminal response"""
    mock_state = {"key": "value"}
    swe_agent.terminal.run.return_value = json.dumps(mock_state)

    await swe_agent._format_instruction()
    swe_agent.terminal.run.assert_called_with('state')
    assert isinstance(swe_agent.cmd_prompt_current_state, str)


@pytest.mark.asyncio
async def test_format_instruction_error(swe_agent):
    """Test _format_instruction with invalid JSON response"""
    swe_agent.terminal.run.return_value = 'invalid json'

    with pytest.raises(json.JSONDecodeError):
        await swe_agent._format_instruction()


@pytest.mark.asyncio
async def test_act_with_eval(swe_agent):
    """Test _act method with run_eval=True"""
    swe_agent.run_eval = True
    swe_agent._parse_commands_for_eval = AsyncMock()

    result = await swe_agent._act()
    assert isinstance(result, Message)
    swe_agent._parse_commands_for_eval.assert_called_once()


@pytest.mark.asyncio
async def test_act_without_eval(swe_agent):
    """Test _act method with run_eval=False"""
    swe_agent.run_eval = False
    swe_agent._parse_commands_for_eval = AsyncMock()

    result = await swe_agent._act()
    assert isinstance(result, Message)
    swe_agent._parse_commands_for_eval.assert_not_called()


@pytest.mark.asyncio
async def test_parse_commands_for_eval_with_diff(swe_agent, mock_extract_patch):
    """Test _parse_commands_for_eval with git diff output"""
    swe_agent.rc.todo = False
    swe_agent.terminal.run.return_value = 'test diff output'

    await swe_agent._parse_commands_for_eval()
    assert swe_agent.output_diff == 'test_patch'
    mock_extract_patch.assert_called_with('test diff output')


@pytest.mark.asyncio
async def test_parse_commands_for_eval_with_error(swe_agent):
    """Test _parse_commands_for_eval error handling"""
    swe_agent.rc.todo = False
    swe_agent.terminal.run.side_effect = Exception('test error')

    await swe_agent._parse_commands_for_eval()
    assert swe_agent.output_diff == ''


@pytest.mark.asyncio
async def test_parse_commands_for_eval_with_todo(swe_agent):
    """Test _parse_commands_for_eval when todo is True"""
    swe_agent.rc.todo = True

    await swe_agent._parse_commands_for_eval()
    swe_agent.terminal.run.assert_not_called()


def test_retrieve_experience(swe_agent):
    """Test _retrieve_experience returns MINIMAL_EXAMPLE"""
    from metagpt.prompts.di.swe_agent import MINIMAL_EXAMPLE

    result = swe_agent._retrieve_experience()
    assert result == MINIMAL_EXAMPLE


def test_update_tool_execution(swe_agent):
    """Test _update_tool_execution adds required tools"""
    swe_agent._update_tool_execution()

    assert 'Bash.run' in swe_agent.tool_execution_map
    assert 'git_create_pull' in swe_agent.tool_execution_map
    assert swe_agent.tool_execution_map['Bash.run'] == swe_agent.terminal.run