# -*- coding: utf-8 -*-
# @Date    : 12/12/2023 4:17 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import os
import json

from metagpt.utils.save_code import save_code_file, DATA_PATH


def test_save_code_file_python():
    save_code_file("example", "print('Hello, World!')")
    file_path = DATA_PATH / "output" / "example" / "code.py"
    assert os.path.exists(file_path), f"File does not exist: {file_path}"


def test_save_code_file_python():
    save_code_file("example", "print('Hello, World!')")
    file_path = DATA_PATH / "output" / "example" / "code.py"
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
