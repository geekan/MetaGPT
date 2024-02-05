import pytest

from metagpt.tools.tool_registry import ToolRegistry
from metagpt.tools.tool_type import ToolType


@pytest.fixture
def tool_registry():
    return ToolRegistry()


@pytest.fixture
def tool_registry_full():
    return ToolRegistry(tool_types=ToolType)


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


class TestClassTool:
    """test class"""

    def test_class_fn(self):
        """test class fn"""
        pass


def test_fn():
    """test function"""
    pass


# Test Tool Registration Class
def test_register_tool_class(tool_registry):
    tool_registry.register_tool("TestClassTool", "/path/to/tool", tool_source_object=TestClassTool)
    assert "TestClassTool" in tool_registry.tools


# Test Tool Registration Function
def test_register_tool_fn(tool_registry):
    tool_registry.register_tool("test_fn", "/path/to/tool", tool_source_object=test_fn)
    assert "test_fn" in tool_registry.tools


# Test Tool Existence Checks
def test_has_tool(tool_registry):
    tool_registry.register_tool("TestClassTool", "/path/to/tool", tool_source_object=TestClassTool)
    assert tool_registry.has_tool("TestClassTool")
    assert not tool_registry.has_tool("NonexistentTool")


# Test Tool Retrieval
def test_get_tool(tool_registry):
    tool_registry.register_tool("TestClassTool", "/path/to/tool", tool_source_object=TestClassTool)
    tool = tool_registry.get_tool("TestClassTool")
    assert tool is not None
    assert tool.name == "TestClassTool"
    assert tool.path == "/path/to/tool"
    assert "description" in tool.schemas


# Similar tests for has_tool_type, get_tool_type, get_tools_by_type
def test_has_tool_type(tool_registry_full):
    assert tool_registry_full.has_tool_type("data_preprocess")
    assert not tool_registry_full.has_tool_type("NonexistentType")


def test_get_tool_type(tool_registry_full):
    retrieved_type = tool_registry_full.get_tool_type("data_preprocess")
    assert retrieved_type is not None
    assert retrieved_type.name == "data_preprocess"


def test_get_tools_by_type(tool_registry):
    tool_type_name = "TestType"
    tool_name = "TestTool"
    tool_path = "/path/to/tool"

    tool_registry.register_tool(tool_name, tool_path, tool_type=tool_type_name, tool_source_object=TestClassTool)

    tools_by_type = tool_registry.get_tools_by_type(tool_type_name)
    assert tools_by_type is not None
    assert tool_name in tools_by_type


# Test case for when the tool type does not exist
def test_get_tools_by_nonexistent_type(tool_registry):
    tools_by_type = tool_registry.get_tools_by_type("NonexistentType")
    assert not tools_by_type
