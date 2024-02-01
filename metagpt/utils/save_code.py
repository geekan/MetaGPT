# -*- coding: utf-8 -*-
# @Date    : 12/12/2023 4:14 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import os

import nbformat

from metagpt.const import DATA_PATH
from metagpt.utils.common import write_json_file


def save_code_file(name: str, code_context: str, file_format: str = "py") -> None:
    """
    Save code files to a specified path.

    Args:
    - name (str): The name of the folder to save the files.
    - code_context (str): The code content.
    - file_format (str, optional): The file format. Supports 'py' (Python file), 'json' (JSON file), and 'ipynb' (Jupyter Notebook file). Default is 'py'.


    Returns:
    - None
    """
    # Create the folder path if it doesn't exist
    os.makedirs(name=DATA_PATH / "output" / f"{name}", exist_ok=True)

    # Choose to save as a Python file or a JSON file based on the file format
    file_path = DATA_PATH / "output" / f"{name}/code.{file_format}"
    if file_format == "py":
        file_path.write_text(code_context + "\n\n", encoding="utf-8")
    elif file_format == "json":
        # Parse the code content as JSON and save
        data = {"code": code_context}
        write_json_file(file_path, data, encoding="utf-8", indent=2)
    elif file_format == "ipynb":
        nbformat.write(code_context, file_path)
    else:
        raise ValueError("Unsupported file format. Please choose 'py', 'json', or 'ipynb'.")
