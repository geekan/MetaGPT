import pytest

from metagpt.tools.tool_registry import ToolRegistry
from metagpt.tools.tool_types import ToolTypes


@pytest.fixture
def tool_registry():
    return ToolRegistry()


@pytest.fixture
def tool_registry_full():
    return ToolRegistry(tool_types=ToolTypes)


@pytest.fixture
def schema_yaml(mocker):
    mock_yaml_content = """
    tool_name:
        key1: value1
        key2: value2
    """
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=mock_yaml_content))
    return mocker


# Test Initialization
def test_initialization(tool_registry):
    assert isinstance(tool_registry, ToolRegistry)
    assert tool_registry.tools == {}
    assert tool_registry.tool_types == {}
    assert tool_registry.tools_by_types == {}


# Test Initialization with tool types
def test_initialize_with_tool_types(tool_registry_full):
    assert isinstance(tool_registry_full, ToolRegistry)
    assert tool_registry_full.tools == {}
    assert tool_registry_full.tools_by_types == {}
    assert "data_preprocess" in tool_registry_full.tool_types


# Test Tool Registration
def test_register_tool(tool_registry, schema_yaml):
    tool_registry.register_tool("TestTool", "/path/to/tool")
    assert "TestTool" in tool_registry.tools


# Test Tool Registration with Non-existing Schema
def test_register_tool_no_schema(tool_registry, mocker):
    mocker.patch("os.path.exists", return_value=False)
    tool_registry.register_tool("TestTool", "/path/to/tool")
    assert "TestTool" not in tool_registry.tools


# Test Tool Existence Checks
def test_has_tool(tool_registry, schema_yaml):
    tool_registry.register_tool("TestTool", "/path/to/tool")
    assert tool_registry.has_tool("TestTool")
    assert not tool_registry.has_tool("NonexistentTool")


# Test Tool Retrieval
def test_get_tool(tool_registry, schema_yaml):
    tool_registry.register_tool("TestTool", "/path/to/tool")
    tool = tool_registry.get_tool("TestTool")
    assert tool is not None
    assert tool.name == "TestTool"
    assert tool.path == "/path/to/tool"


# Similar tests for has_tool_type, get_tool_type, get_tools_by_type
def test_has_tool_type(tool_registry_full):
    assert tool_registry_full.has_tool_type("data_preprocess")
    assert not tool_registry_full.has_tool_type("NonexistentType")


def test_get_tool_type(tool_registry_full):
    retrieved_type = tool_registry_full.get_tool_type("data_preprocess")
    assert retrieved_type is not None
    assert retrieved_type.name == "data_preprocess"


def test_get_tools_by_type(tool_registry, schema_yaml):
    tool_type_name = "TestType"
    tool_name = "TestTool"
    tool_path = "/path/to/tool"

    tool_registry.register_tool(tool_name, tool_path, tool_type=tool_type_name)

    tools_by_type = tool_registry.get_tools_by_type(tool_type_name)
    assert tools_by_type is not None
    assert tool_name in tools_by_type


# Test case for when the tool type does not exist
def test_get_tools_by_nonexistent_type(tool_registry):
    tools_by_type = tool_registry.get_tools_by_type("NonexistentType")
    assert not tools_by_type
