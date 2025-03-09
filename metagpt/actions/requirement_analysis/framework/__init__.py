#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : __init__.py
@Desc    : The implementation of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List

from pydantic import BaseModel

from metagpt.actions.requirement_analysis.framework.evaluate_framework import EvaluateFramework
from metagpt.actions.requirement_analysis.framework.write_framework import WriteFramework
from metagpt.config2 import config
from metagpt.utils.common import awrite


async def save_framework(
    dir_data: str, trd: Optional[str] = None, output_dir: Optional[Union[str, Path]] = None
) -> List[str]:
    """
    Saves framework data to files based on input JSON data and optionally saves a TRD (technical requirements document).

    Args:
        dir_data (str): JSON data in string format enclosed in triple backticks ("```json" "...data..." "```").
        trd (str, optional): Technical requirements document content to be saved. Defaults to None.
        output_dir (Union[str, Path], optional): Output directory path where files will be saved. If not provided,
            a default directory is created based on the current timestamp and a random UUID suffix.

    Returns:
        List[str]: List of file paths where data was saved.

    Raises:
        Any exceptions raised during file writing operations.

    Notes:
        - JSON data should be provided in the format "```json ...data... ```".
        - The function ensures that paths and filenames are correctly formatted and creates necessary directories.

    Example:
        ```python
        dir_data = "```json\n[{\"path\": \"/folder\", \"filename\": \"file1.txt\", \"content\": \"Some content\"}]\n```"
        trd = "Technical requirements document content."
        output_dir = '/path/to/output/dir'
        saved_files = await save_framework(dir_data, trd, output_dir)
        print(saved_files)
        ```
    """
    output_dir = (
        Path(output_dir)
        if output_dir
        else config.workspace.path / (datetime.now().strftime("%Y%m%d%H%M%ST") + uuid.uuid4().hex[0:8])
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    json_data = dir_data.removeprefix("```json").removesuffix("```")
    items = json.loads(json_data)

    class Data(BaseModel):
        path: str
        filename: str
        content: str

    if trd:
        pathname = output_dir / "TRD.md"
        await awrite(filename=pathname, data=trd)

    files = []
    for i in items:
        v = Data.model_validate(i)
        if v.path and v.path[0] == "/":
            v.path = "." + v.path
        pathname = output_dir / v.path
        pathname.mkdir(parents=True, exist_ok=True)
        pathname = pathname / v.filename
        await awrite(filename=pathname, data=v.content)
        files.append(str(pathname))
    return files


__all__ = [WriteFramework, EvaluateFramework]
