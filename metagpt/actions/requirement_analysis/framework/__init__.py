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
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import awrite


@register_tool(tags=["software framework"])
async def save_framework(dir_data: str, output_dir: Optional[Union[str, Path]] = None) -> List[str]:
    output_dir = (
        Path(output_dir)
        if output_dir
        else DEFAULT_WORKSPACE_ROOT / (datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[0:8])
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    json_data = dir_data.removeprefix("```json").removesuffix("```")
    items = json.loads(json_data)

    class Data(BaseModel):
        path: str
        filename: str
        content: str

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
