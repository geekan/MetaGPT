#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/17 17:58
@Author  : alexanderwu
@File    : repo_parser.py
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from pprint import pformat
from typing import List

import pandas as pd
from pydantic import BaseModel, Field

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.utils.common import any_to_str
from metagpt.utils.exceptions import handle_exception


class RepoParser(BaseModel):
    base_directory: Path = Field(default=None)

    @classmethod
    @handle_exception(exception_type=Exception, default_return=[])
    def _parse_file(cls, file_path: Path) -> list:
        """Parse a Python file in the repository."""
        return ast.parse(file_path.read_text()).body

    def extract_class_and_function_info(self, tree, file_path):
        """Extract class, function, and global variable information from the AST."""
        file_info = {
            "file": str(file_path.relative_to(self.base_directory)),
            "classes": [],
            "functions": [],
            "globals": [],
        }

        page_info = []
        for node in tree:
            info = RepoParser.node_to_str(node)
            page_info.append(info)
            if isinstance(node, ast.ClassDef):
                class_methods = [m.name for m in node.body if is_func(m)]
                file_info["classes"].append({"name": node.name, "methods": class_methods})
            elif is_func(node):
                file_info["functions"].append(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                    if isinstance(target, ast.Name):
                        file_info["globals"].append(target.id)
        file_info["page_info"] = page_info
        return file_info

    def generate_symbols(self):
        files_classes = []
        directory = self.base_directory

        matching_files = []
        extensions = ["*.py", "*.js"]
        for ext in extensions:
            matching_files += directory.rglob(ext)
        for path in matching_files:
            tree = self._parse_file(path)
            file_info = self.extract_class_and_function_info(tree, path)
            files_classes.append(file_info)

        return files_classes

    def generate_json_structure(self, output_path):
        """Generate a JSON file documenting the repository structure."""
        files_classes = self.generate_symbols()
        output_path.write_text(json.dumps(files_classes, indent=4))

    def generate_dataframe_structure(self, output_path):
        """Generate a DataFrame documenting the repository structure and save as CSV."""
        files_classes = self.generate_symbols()
        df = pd.DataFrame(files_classes)
        df.to_csv(output_path, index=False)

    def generate_structure(self, output_path=None, mode="json"):
        """Generate the structure of the repository as a specified format."""
        output_file = self.base_directory / f"{self.base_directory.name}-structure.{mode}"
        output_path = Path(output_path) if output_path else output_file

        if mode == "json":
            self.generate_json_structure(output_path)
        elif mode == "csv":
            self.generate_dataframe_structure(output_path)

    @staticmethod
    def node_to_str(node) -> (int, int, str, str | List):
        def _parse_name(n):
            if n.asname:
                return f"{n.name} as {n.asname}"
            return n.name

        if any_to_str(node) == any_to_str(ast.Expr):
            return node.lineno, node.end_lineno, any_to_str(node), RepoParser._parse_expr(node)
        mappings = {
            any_to_str(ast.Import): lambda x: [_parse_name(n) for n in x.names],
            any_to_str(ast.Assign): lambda x: [n.id for n in x.targets],
            any_to_str(ast.ClassDef): lambda x: x.name,
            any_to_str(ast.FunctionDef): lambda x: x.name,
            any_to_str(ast.ImportFrom): lambda x: {"module": x.module, "names": [_parse_name(n) for n in x.names]},
            any_to_str(ast.If): lambda x: x.test.left.id,
        }
        func = mappings.get(any_to_str(node))
        if func:
            return node.lineno, node.end_lineno, any_to_str(node), func(node)
        return node.lineno, node.end_lineno, any_to_str(node), None

    @staticmethod
    def _parse_expr(node) -> (int, int, str, str | List):
        if isinstance(node.value, ast.Constant):
            return any_to_str(ast.Constant), node.value.value
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                return any_to_str(ast.Call), f"{node.value.func.value.id}.{node.value.func.attr}"
            if isinstance(node.value.func, ast.Name):
                return any_to_str(ast.Call), node.value.func.id
        return any_to_str(node.value), None


def is_func(node):
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))


def main():
    repo_parser = RepoParser(base_directory=CONFIG.workspace_path / "web_2048")
    symbols = repo_parser.generate_symbols()
    logger.info(pformat(symbols))


def error():
    """raise Exception and logs it"""
    RepoParser._parse_file(Path("test.py"))


if __name__ == "__main__":
    error()
