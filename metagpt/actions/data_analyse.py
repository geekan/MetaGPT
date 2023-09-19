#!/usr/bin/env python

from __future__ import annotations

import asyncio
import json
from typing import Callable
from pydantic import parse_obj_as
import pandas as pd

from metagpt.actions import Action
from metagpt.config import CONFIG
from metagpt.logs import logger

from metagpt.const import WORKSPACE_ROOT
from metagpt.actions import WriteDesign
from metagpt.actions.action import Action
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed

PROMPT_TEMPLATE = """
NOTICE
1. Role: You are a data scientist; the main goal is to write python code for data processing and visualization. 
2. Requirement: You are provided with a pandas dataframe with metadata information. Your code most likely uses data science packages such as pandas, numpy, matplotlib, etc.
3. Attention1: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".
4. Attention2: Use 'pandas' package to process dataframe.
5. Attention3: Use 'matplotlib' package to visualize data.
6. Attention4: Save the processed dataframe and the chart in {workspace}/output/.
-----

You are provided with the following pandas DataFrame with the following metadata:
{metadata}

update the python code based on the last user question:
{context}

```python
# import all the dependencies required  
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# def process_data(df):
    # code here
    return df 

result = process_data(df)
```
"""


class DataAnalyse(Action):
    def __init__(self, name="DataAnalyse", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, file_path):
        df = self._read_file(file_path)
        prompt = PROMPT_TEMPLATE.format(metadata=str(df.head()), context=context, workspace=WORKSPACE_ROOT)
        code = await self.write_code(prompt)
        return code

    def _read_file(self, file_path):
        if file_path.endswith(".csv"):
            return pd.read_csv(file_path)
        elif file_path.endswith(".xlsx"):
            return pd.read_excel(file_path)
        else:
            raise ValueError("Invalid file format.")

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

