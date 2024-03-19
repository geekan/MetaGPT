import pytest

from metagpt.tools.tool_registry import ToolRegistry


@pytest.fixture
def tool_registry():
    return ToolRegistry()


# Test Initialization
def test_initialization(tool_registry):
    assert isinstance(tool_registry, ToolRegistry)
    assert tool_registry.tools == {}
    assert tool_registry.tools_by_tags == {}


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


def test_has_tool_tag(tool_registry):
    tool_registry.register_tool(
        "TestClassTool", "/path/to/tool", tool_source_object=TestClassTool, tags=["machine learning", "test"]
    )
    assert tool_registry.has_tool_tag("test")
    assert not tool_registry.has_tool_tag("Non-existent tag")


def test_get_tools_by_tag(tool_registry):
    tool_tag_name = "Test Tag"
    tool_name = "TestTool"
    tool_path = "/path/to/tool"

    tool_registry.register_tool(tool_name, tool_path, tags=[tool_tag_name], tool_source_object=TestClassTool)

    tools_by_tag = tool_registry.get_tools_by_tag(tool_tag_name)
    assert tools_by_tag is not None
    assert tool_name in tools_by_tag

    tools_by_tag_non_existent = tool_registry.get_tools_by_tag("Non-existent Tag")
    assert not tools_by_tag_non_existent
