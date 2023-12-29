from __future__ import annotations

from typing import Union

import libcst as cst
from libcst._nodes.module import Module

DocstringNode = Union[cst.Module, cst.ClassDef, cst.FunctionDef]


def get_docstring_statement(body: DocstringNode) -> cst.SimpleStatementLine:
    """Extracts the docstring from the body of a node.

    Args:
        body: The body of a node.

    Returns:
        The docstring statement if it exists, None otherwise.
    """
    if isinstance(body, cst.Module):
        body = body.body
    else:
        body = body.body.body

    if not body:
        return

    statement = body[0]
    if not isinstance(statement, cst.SimpleStatementLine):
        return

    expr = statement
    while isinstance(expr, (cst.BaseSuite, cst.SimpleStatementLine)):
        if len(expr.body) == 0:
            return None
        expr = expr.body[0]

    if not isinstance(expr, cst.Expr):
        return None

    val = expr.value
    if not isinstance(val, (cst.SimpleString, cst.ConcatenatedString)):
        return None

    evaluated_value = val.evaluated_value
    if isinstance(evaluated_value, bytes):
        return None

    return statement


def has_decorator(node: DocstringNode, name: str) -> bool:
    return hasattr(node, "decorators") and any(
        (hasattr(i.decorator, "value") and i.decorator.value == name)
        or (hasattr(i.decorator, "func") and hasattr(i.decorator.func, "value") and i.decorator.func.value == name)
        for i in node.decorators
    )


class DocstringCollector(cst.CSTVisitor):
    """A visitor class for collecting docstrings from a CST.

    Attributes:
        stack: A list to keep track of the current path in the CST.
        docstrings: A dictionary mapping paths in the CST to their corresponding docstrings.
    """

    def __init__(self):
        self.stack: list[str] = []
        self.docstrings: dict[tuple[str, ...], cst.SimpleStatementLine] = {}

    def visit_Module(self, node: cst.Module) -> bool | None:
        self.stack.append("")

    def leave_Module(self, node: cst.Module) -> None:
        return self._leave(node)

    def visit_ClassDef(self, node: cst.ClassDef) -> bool | None:
        self.stack.append(node.name.value)

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        return self._leave(node)

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
        self.stack.append(node.name.value)

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        return self._leave(node)

    def _leave(self, node: DocstringNode) -> None:
        key = tuple(self.stack)
        self.stack.pop()
        if has_decorator(node, "overload"):
            return

        statement = get_docstring_statement(node)
        if statement:
            self.docstrings[key] = statement


class DocstringTransformer(cst.CSTTransformer):
    """A transformer class for replacing docstrings in a CST.

    Attributes:
        stack: A list to keep track of the current path in the CST.
        docstrings: A dictionary mapping paths in the CST to their corresponding docstrings.
    """

    def __init__(
        self,
        docstrings: dict[tuple[str, ...], cst.SimpleStatementLine],
    ):
        self.stack: list[str] = []
        self.docstrings = docstrings

    def visit_Module(self, node: cst.Module) -> bool | None:
        self.stack.append("")

    def leave_Module(self, original_node: Module, updated_node: Module) -> Module:
        return self._leave(original_node, updated_node)

    def visit_ClassDef(self, node: cst.ClassDef) -> bool | None:
        self.stack.append(node.name.value)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.CSTNode:
        return self._leave(original_node, updated_node)

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
        self.stack.append(node.name.value)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.CSTNode:
        return self._leave(original_node, updated_node)

    def _leave(self, original_node: DocstringNode, updated_node: DocstringNode) -> DocstringNode:
        key = tuple(self.stack)
        self.stack.pop()

        if has_decorator(updated_node, "overload"):
            return updated_node

        statement = self.docstrings.get(key)
        if not statement:
            return updated_node

        original_statement = get_docstring_statement(original_node)

        if isinstance(updated_node, cst.Module):
            body = updated_node.body
            if original_statement:
                return updated_node.with_changes(body=(statement, *body[1:]))
            else:
                updated_node = updated_node.with_changes(body=(statement, cst.EmptyLine(), *body))
                return updated_node

        body = updated_node.body.body[1:] if original_statement else updated_node.body.body
        return updated_node.with_changes(body=updated_node.body.with_changes(body=(statement, *body)))


def merge_docstring(code: str, documented_code: str) -> str:
    """Merges the docstrings from the documented code into the original code.

    Args:
        code: The original code.
        documented_code: The documented code.

    Returns:
        The original code with the docstrings from the documented code.
    """
    code_tree = cst.parse_module(code)
    documented_code_tree = cst.parse_module(documented_code)

    visitor = DocstringCollector()
    documented_code_tree.visit(visitor)
    transformer = DocstringTransformer(visitor.docstrings)
    modified_tree = code_tree.visit(transformer)
    return modified_tree.code
