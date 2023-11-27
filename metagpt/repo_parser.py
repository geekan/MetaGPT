#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/17 17:58
@Author  : alexanderwu
@File    : repo_parser.py
"""
import json
from pathlib import Path

import ast
import pandas as pd
from pydantic import BaseModel, Field
from pprint import pformat

from metagpt.config import CONFIG
from metagpt.logs import logger


class RepoParser(BaseModel):
    base_directory: Path = Field(default=None)

    def parse_file(self, file_path):
        """Parse a Python file in the repository."""
        try:
            return ast.parse(file_path.read_text()).body
        except:
            return []

    def extract_class_and_function_info(self, tree, file_path):
        """Extract class, function, and global variable information from the AST."""
        file_info = {
            "file": str(file_path.relative_to(self.base_directory)),
            "classes": [],
            "functions": [],
            "globals": []
        }

        for node in tree:
            if isinstance(node, ast.ClassDef):
                class_methods = [m.name for m in node.body if is_func(m)]
                file_info["classes"].append({"name": node.name, "methods": class_methods})
            elif is_func(node):
                file_info["functions"].append(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                    if isinstance(target, ast.Name):
                        file_info["globals"].append(target.id)
        return file_info

    def generate_symbols(self):
        files_classes = []
        directory = self.base_directory
        for path in directory.rglob('*.py'):
            tree = self.parse_file(path)
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

    def generate_structure(self, output_path=None, mode='json'):
        """Generate the structure of the repository as a specified format."""
        output_file = self.base_directory / f"{self.base_directory.name}-structure.{mode}"
        output_path = Path(output_path) if output_path else output_file

        if mode == 'json':
            self.generate_json_structure(output_path)
        elif mode == 'csv':
            self.generate_dataframe_structure(output_path)


def is_func(node):
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))


def main():
    repo_parser = RepoParser(base_directory=CONFIG.workspace_path / "web_2048")
    symbols = repo_parser.generate_symbols()
    logger.info(pformat(symbols))


if __name__ == '__main__':
    main()
