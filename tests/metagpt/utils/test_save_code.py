# -*- coding: utf-8 -*-
# @Date    : 12/12/2023 4:17 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import json
import os

import nbformat
import pytest

from metagpt.actions.execute_code import ExecutePyCode
from metagpt.utils.save_code import DATA_PATH, save_code_file


def test_save_code_file_python():
    save_code_file("example", "print('Hello, World!')")
    file_path = DATA_PATH / "output" / "example" / "code.py"
    assert os.path.exists(file_path), f"File does not exist: {file_path}"
    with open(file_path, "r", encoding="utf-8") as fp:
        content = fp.read()
    assert "print('Hello, World!')" in content, "File content does not match"


def test_save_code_file_json():
    save_code_file("example_json", "print('Hello, JSON!')", file_format="json")
    file_path = DATA_PATH / "output" / "example_json" / "code.json"
    with open(file_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    assert "code" in data, "JSON key 'code' is missing"
    assert data["code"] == "print('Hello, JSON!')", "JSON content does not match"


@pytest.mark.asyncio
async def test_save_code_file_notebook():
    code = "print('Hello, World!')"
    executor = ExecutePyCode()
    await executor.run(code)
    # Save as a Notebook file
    save_code_file("example_nb", executor.nb, file_format="ipynb")
    file_path = DATA_PATH / "output" / "example_nb" / "code.ipynb"
    assert os.path.exists(file_path), f"Notebook file does not exist: {file_path}"

    # Additional checks specific to notebook format
    notebook = nbformat.read(file_path, as_version=4)
    assert len(notebook.cells) > 0, "Notebook should have at least one cell"
    first_cell_source = notebook.cells[0].source
    assert "print('Hello, World!')" in first_cell_source, "Notebook cell content does not match"
