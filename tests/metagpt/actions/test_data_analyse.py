#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/19
@Author  : rainyrfeng
@File    : test_data_analyse.py
"""
import pytest
import pandas as pd
from metagpt.actions.data_analyse import DataAnalyse


@pytest.mark.asyncio
async def test_read_file():
    df = await DataAnalyse()._read_file("../tests/data/data_for_test.csv")
    assert type(df) == pd.core.frame.DataFrame


@pytest.mark.asyncio
async def test_run():
    res = await DataAnalyse().run("../tests/data/data_for_test.csv", "Which are the 5 happiest countries?")
    assert "import pandas as pd" in res
