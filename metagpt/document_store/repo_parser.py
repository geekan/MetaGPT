#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/17 17:58
@Author  : alexanderwu
@File    : repo_parser.py
"""
import json
import pathlib
import ast

import pandas as pd


class RepoParser:
    def __init__(self):
        self.base_directory = None

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
            elif isinstance(node, ast.Assign) or isinstance(node, ast.AnnAssign):
                for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                    if isinstance(target, ast.Name):
                        file_info["globals"].append(target.id)
        return file_info

    def generate_json_structure(self, directory, output_path):
        """Generate a JSON file documenting the repository structure."""
        files_classes = []
        for path in directory.rglob('*.py'):
            tree = self.parse_file(path)
            file_info = self.extract_class_and_function_info(tree, path)
            files_classes.append(file_info)

        output_path.write_text(json.dumps(files_classes, indent=4))

    def generate_dataframe_structure(self, directory, output_path):
        """Generate a DataFrame documenting the repository structure and save as CSV."""
        files_classes = []
        for path in directory.rglob('*.py'):
            tree = self.parse_file(path)
            file_info = self.extract_class_and_function_info(tree, path)
            files_classes.append(file_info)

        df = pd.DataFrame(files_classes)
        df.to_csv(output_path, index=False)

    def generate_structure(self, directory_path, output_path=None, mode='json'):
        """Generate the structure of the repository as a specified format."""
        self.base_directory = pathlib.Path(directory_path)
        output_file = self.base_directory / f"{self.base_directory.name}-structure.{mode}"
        output_path = pathlib.Path(output_path) if output_path else output_file

        if mode == 'json':
            self.generate_json_structure(self.base_directory, output_path)
        elif mode == 'csv':
            self.generate_dataframe_structure(self.base_directory, output_path)


def is_func(node):
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))


def main():
    repo_parser = RepoParser()
    repo_parser.generate_structure("/Users/alexanderwu/git/mg1/metagpt", "/Users/alexanderwu/git/mg1/mg1-structure.csv", mode='csv')


if __name__ == '__main__':
    main()
