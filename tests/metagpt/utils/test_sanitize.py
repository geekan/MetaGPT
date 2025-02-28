# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

import pytest

from metagpt.utils.sanitize import (
    NodeType,
    code_extract,
    get_definition_name,
    get_deps,
    get_function_dependency,
    has_return_statement,
    sanitize,
    syntax_check,
    traverse_tree,
)


@pytest.fixture
def mock_node():
    node = Mock()
    node.type = "test_node"
    node.text = b"test_text"
    node.children = []
    return node


def test_node_type_enum():
    assert NodeType.CLASS.value == "class_definition"
    assert NodeType.FUNCTION.value == "function_definition"
    assert isinstance(NodeType.IMPORT.value, list)


@patch("tree_sitter.Node")
def test_traverse_tree(mock_node_class):
    # 测试基本情况：没有子节点的情况
    root = Mock()
    cursor = Mock()
    cursor.node = root
    cursor.goto_first_child.return_value = False
    cursor.goto_next_sibling.return_value = False
    cursor.goto_parent.return_value = False
    root.walk.return_value = cursor

    nodes = list(traverse_tree(root))
    assert len(nodes) == 1
    assert nodes[0] == root

    # 测试有子节点和兄弟节点的情况
    cursor2 = Mock()
    cursor2.node = Mock()

    # 模拟遍历行为
    first_child_calls = [True, False]
    next_sibling_calls = [False]
    parent_calls = [True, False]

    cursor2.goto_first_child.side_effect = lambda: first_child_calls.pop(0) if first_child_calls else False
    cursor2.goto_next_sibling.side_effect = lambda: next_sibling_calls.pop(0) if next_sibling_calls else False
    cursor2.goto_parent.side_effect = lambda: parent_calls.pop(0) if parent_calls else False

    root2 = Mock()
    root2.walk.return_value = cursor2
    nodes = list(traverse_tree(root2))
    assert len(nodes) > 1


def test_syntax_check():
    # 测试有效代码
    assert syntax_check("def test(): return True") is True

    # 测试无效代码
    assert syntax_check("def test() return True") is False

    # 测试无效代码（带verbose）
    assert syntax_check("def test() return True", verbose=True) is False

    # 测试内存错误情况
    with patch("ast.parse", side_effect=MemoryError):
        assert syntax_check("large_code", verbose=True) is False


def test_code_extract():
    # 测试基本情况
    text = "def valid_function():\n    return True\n"
    result = code_extract(text)
    assert syntax_check(result)
    assert "def valid_function" in result

    # 测试空字符串
    assert code_extract("") == ""

    # 测试单行有效语法
    single_line = "x = 1"
    result = code_extract(single_line)
    assert syntax_check(result)
    assert "x = 1" in result

    # 测试完全无效的代码
    assert code_extract("invalid!!!!") == "" or code_extract("invalid!!!!") == "invalid!!!!"

    # 测试带有嵌套结构的有效代码
    nested_code = """def outer():\n    def inner():\n        return True\n"""
    result = code_extract(nested_code)
    assert syntax_check(result)
    assert "def outer" in result


def test_get_definition_name():
    # 基本测试
    mock_identifier = Mock()
    mock_identifier.type = NodeType.IDENTIFIER.value
    mock_identifier.text = b"test_function"

    mock_node = Mock()
    mock_node.children = [mock_identifier]
    assert get_definition_name(mock_node) == "test_function"

    # 测试空children
    mock_node.children = []
    assert get_definition_name(mock_node) is None

    # 测试children中没有identifier
    mock_node.children = [Mock(type="not_identifier")]
    assert get_definition_name(mock_node) is None


@pytest.mark.parametrize(
    "node_type,expected",
    [
        (NodeType.RETURN.value, True),
        ("other_type", False),
    ],
)
def test_has_return_statement(node_type, expected):
    mock_node = Mock()
    cursor = Mock()
    cursor.node = Mock()
    cursor.node.type = node_type
    cursor.goto_first_child.return_value = False
    cursor.goto_next_sibling.return_value = False
    cursor.goto_parent.return_value = False
    mock_node.walk.return_value = cursor

    assert has_return_statement(mock_node) is expected


def test_get_deps():
    mock_id1 = Mock(type=NodeType.IDENTIFIER.value, text=b"dep1")
    mock_id2 = Mock(type=NodeType.IDENTIFIER.value, text=b"dep2")
    mock_node = Mock(children=[mock_id1, mock_id2])

    nodes = [("test_func", mock_node)]
    result = get_deps(nodes)

    assert "test_func" in result
    assert result["test_func"] == {"dep1", "dep2"}

    # 测试嵌套结构
    nested_node = Mock(children=[Mock(type="not_identifier", children=[mock_id1])])
    nodes = [("nested_func", nested_node)]
    result = get_deps(nodes)
    assert result["nested_func"] == {"dep1"}


def test_get_function_dependency():
    call_graph = {"main": {"helper1", "helper2"}, "helper1": {"helper3"}, "helper2": set(), "helper3": set()}

    result = get_function_dependency("main", call_graph)
    assert result == {"main", "helper1", "helper2", "helper3"}

    assert get_function_dependency("non_existent", call_graph) == {"non_existent"}


@patch("tree_sitter.Parser")
@patch("tree_sitter.Language")
def test_sanitize(mock_language, mock_parser):
    test_code = """import math
from os import path

class TestClass:
    def method(self): return True

def test_function():
    return True

x = 1"""

    mock_root = Mock()
    mock_nodes = []

    # 添加导入语句
    import_node = Mock(type="import_statement", start_byte=0, end_byte=11)
    import_from_node = Mock(type="import_from_statement", start_byte=12, end_byte=30)
    mock_nodes.extend([import_node, import_from_node])

    # 添加类定义
    class_node = Mock(type="class_definition", start_byte=32, end_byte=80)
    class_id = Mock(type="identifier", text=b"TestClass")
    class_node.children = [class_id]
    mock_nodes.append(class_node)

    # 添加函数定义
    func_node = Mock(type="function_definition", start_byte=82, end_byte=110)
    func_id = Mock(type="identifier", text=b"test_function")
    return_node = Mock(type="return_statement")
    func_node.children = [func_id, return_node]
    mock_nodes.append(func_node)

    # 添加赋值语句
    assign_node = Mock(type="expression_statement", start_byte=112, end_byte=117)
    assign_child = Mock(type="assignment")
    var_id = Mock(type="identifier", text=b"x")
    assign_child.children = [var_id]
    assign_node.children = [assign_child]
    mock_nodes.append(assign_node)

    mock_root.children = mock_nodes
    mock_tree = Mock(root_node=mock_root)
    mock_parser.return_value.parse.return_value = mock_tree

    # 测试无entrypoint情况
    result = sanitize(test_code)
    assert isinstance(result, str)
    assert len(result) > 0

    # 测试有entrypoint情况
    result = sanitize(test_code, entrypoint="test_function")
    assert isinstance(result, str)
    assert len(result) > 0

    # 测试空代码
    assert sanitize("") == ""

    # 测试无效代码
    assert sanitize("invalid code") == "invalid!!!!" or sanitize("invalid code") == ""

    # 测试函数依赖
    mock_nodes = [func_node]  # 只保留函数节点
    mock_root.children = mock_nodes
    result = sanitize(test_code, entrypoint="test_function")
    assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main(["-v"])
