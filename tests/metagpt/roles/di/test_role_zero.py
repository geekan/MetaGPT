from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metagpt.actions import UserRequirement
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message, UserMessage, AIMessage
from metagpt.tools.libs.browser import Browser


class MockConfig:
    """Mock configuration for RoleZero testing"""

    class RoleZeroConfig:
        enable_longterm_memory = True
        longterm_memory_persist_path = "/tmp/test_memory"
        memory_k = 5
        similarity_top_k = 3
        use_llm_ranker = False

    role_zero = RoleZeroConfig()


class MockLLM:
    """Mock LLM for testing"""

    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["Mock LLM Response"]
        self.response_index = 0

    async def aask(self, *args, **kwargs):
        response = self.responses[self.response_index]
        self.response_index = (self.response_index + 1) % len(self.responses)
        return response

    def support_image_input(self):
        return True

    def format_msg(self, msgs):
        return msgs


class MockToolRecommender:
    """Mock tool recommender for testing"""

    async def recommend_tools(self):
        return []


class MockMemory:
    """Mock memory for testing"""

    def add(self, msg):
        pass

    def get(self, k=None):
        return []


@pytest.fixture
def mock_role_zero():
    """Fixture providing a configured RoleZero instance for testing"""
    role = RoleZero()
    role.llm = MockLLM()
    role.config = MockConfig()
    role.tool_recommender = MockToolRecommender()
    role.rc.working_memory = MockMemory()
    role.rc.memory = MockMemory()
    return role


@pytest.fixture
def mock_message():
    """Fixture providing a test message"""
    return Message(content="Test message", role="user")


@pytest.mark.asyncio
async def test_model_validators(mock_role_zero):
    """Test all model validators"""
    # Test set_plan_and_tool
    assert mock_role_zero.react_mode == "react"
    mock_role_zero = await mock_role_zero.set_plan_and_tool()
    assert mock_role_zero.planner is not None

    # Test set_tool_execution
    mock_role_zero = await mock_role_zero.set_tool_execution()
    assert "Plan.append_task" in mock_role_zero.tool_execution_map
    assert "RoleZero.ask_human" in mock_role_zero.tool_execution_map

    # Test set_longterm_memory
    mock_role_zero = await mock_role_zero.set_longterm_memory()
    assert mock_role_zero.rc.memory is not None


@pytest.mark.asyncio
async def test_think_react_cycle(mock_role_zero):
    """Test the think-react cycle"""
    # Setup test conditions
    mock_role_zero.rc.todo = True
    mock_role_zero.planner.plan.goal = "Test goal"
    mock_role_zero.respond_language = "English"

    # Test _think
    with patch('metagpt.roles.di.role_zero.ThoughtReporter'):
        result = await mock_role_zero._think()
        assert result is True

    # Test _react
    mock_role_zero.rc.news = [Message(content="Test", cause_by=UserRequirement())]
    with patch.object(mock_role_zero, '_quick_think', return_value=(None, "TASK")):
        result = await mock_role_zero._react()
        assert isinstance(result, Message)


@pytest.mark.asyncio
async def test_command_parsing(mock_role_zero):
    """Test command parsing functionality"""
    # Test valid JSON parsing
    valid_commands = '''[
        {"command_name": "Editor.read", "args": {"filename": "test.txt"}},
        {"command_name": "Plan.finish_current_task", "args": {}}
    ]'''
    commands, ok, rsp = await mock_role_zero._parse_commands(valid_commands)
    assert ok is True
    assert len(commands) == 2

    # Test invalid JSON
    invalid_commands = "Invalid JSON"
    with patch.object(mock_role_zero.llm, 'aask') as mock_aask:
        mock_aask.return_value = valid_commands
        commands, ok, rsp = await mock_role_zero._parse_commands(invalid_commands)
        assert ok is False


@pytest.mark.asyncio
async def test_command_execution(mock_role_zero):
    """Test command execution"""
    # Test special commands
    special_commands = [
        {"command_name": "Plan.finish_current_task", "args": {}},
        {"command_name": "end", "args": {}}
    ]

    with patch.object(mock_role_zero, '_run_special_command') as mock_special:
        mock_special.return_value = "Special command executed"
        result = await mock_role_zero._run_commands(special_commands)
        assert "Command Plan.finish_current_task executed" in result

    # Test normal commands
    normal_commands = [
        {"command_name": "Editor.read", "args": {"filename": "test.txt"}}
    ]
    with patch.object(mock_role_zero.editor, 'read', return_value="File content"):
        result = await mock_role_zero._run_commands(normal_commands)
        assert "Command Editor.read executed" in result


@pytest.mark.asyncio
async def test_message_handling(mock_role_zero):
    """Test message parsing and handling"""
    # Test browser action parsing
    mock_browser = AsyncMock(spec=Browser)
    mock_browser.is_empty_page = False
    mock_browser.view.return_value = "Browser content"
    mock_role_zero.browser = mock_browser

    browser_memory = [
        UserMessage(content="Command Browser.goto executed"),
        UserMessage(content="Other message")
    ]
    result = await mock_role_zero.parse_browser_actions(browser_memory)
    assert len(result) == 3

    # Test editor result parsing
    editor_memory = [
        UserMessage(content="Command Editor.read executed: content"),
        UserMessage(content="Normal message")
    ]
    result = await mock_role_zero.parse_editor_result(editor_memory)
    assert len(result) == 2

    # Test image parsing
    image_memory = [
        UserMessage(content="Message with ![image](test.png)"),
        UserMessage(content="Normal message")
    ]
    result = mock_role_zero.parse_images(image_memory)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_error_cases(mock_role_zero):
    """Test error handling in various scenarios"""
    # Test invalid command execution
    invalid_commands = [
        {"command_name": "NonExistentCommand", "args": {}}
    ]
    result = await mock_role_zero._run_commands(invalid_commands)
    assert "Command NonExistentCommand not found" in result

    # Test command parsing with malformed JSON
    malformed_json = '[{"command_name": "test", "args": {}]'  # Missing closing brace
    with patch.object(mock_role_zero.llm, 'aask') as mock_aask:
        mock_aask.return_value = '[{"command_name": "fixed", "args": {}}]'  # Valid JSON response
        commands, ok, rsp = await mock_role_zero._parse_commands(malformed_json)
        assert ok is True

    # Test command parsing with improper command structure
    invalid_format = '[{"not_a_command": true}]'  # Valid JSON but wrong format
    with patch.object(mock_role_zero.llm, 'aask') as mock_aask:
        mock_aask.return_value = invalid_format
        commands, ok, rsp = await mock_role_zero._parse_commands(invalid_format)
        assert ok is False

    # Test think with no todo
    mock_role_zero.rc.todo = False
    result = await mock_role_zero._think()
    assert result is False


@pytest.mark.asyncio
async def test_special_commands(mock_role_zero):
    """Test special command handling"""
    # Test Plan.finish_current_task
    finish_command = {"command_name": "Plan.finish_current_task", "args": {}}
    result = await mock_role_zero._run_special_command(finish_command)
    assert "Current task is finished" in result

    # Test end command
    end_command = {"command_name": "end", "args": {}}
    with patch.object(mock_role_zero.llm, 'aask', return_value="Summary"):
        result = await mock_role_zero._run_special_command(end_command)
        assert result

    # Test ask_human command
    ask_command = {"command_name": "RoleZero.ask_human", "args": {"question": "Test?"}}
    result = await mock_role_zero._run_special_command(ask_command)
    assert "Not in MGXEnv" in result


@pytest.mark.asyncio
async def test_quick_think(mock_role_zero):
    """Test quick think functionality"""
    mock_role_zero.rc.news = [Message(content="Test", cause_by=UserRequirement())]

    with patch.object(mock_role_zero.llm, 'aask') as mock_aask:
        mock_aask.side_effect = ["QUICK", "Quick response"]
        result, intent = await mock_role_zero._quick_think()
        assert isinstance(result, AIMessage)
        assert intent == "QUICK"


@pytest.mark.asyncio
async def test_experience_retrieval(mock_role_zero):
    """Test experience retrieval functionality"""
    # Test with empty memory
    result = mock_role_zero._retrieve_experience()
    assert isinstance(result, str)

    # Test with mock experience retriever
    mock_role_zero.experience_retriever.retrieve = MagicMock(return_value="Test experience")
    result = mock_role_zero._retrieve_experience()
    assert result == "Test experience"
