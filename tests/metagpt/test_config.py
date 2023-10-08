#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : chuchengshen
@File    : test_config.py
"""

import asyncio
import random

import pytest

from metagpt.config import CONFIG


@pytest.mark.asyncio
async def test_config_set_context():
    async def run(i):
        key = f"TOEKN_xx{i}"
        CONFIG.set_context({"OPENAI_API_KEY": key})
        await asyncio.sleep(random.random() / 10)
        assert CONFIG.openai_api_key == key

    await asyncio.wait([run(i) for i in range(4)])


@pytest.mark.asyncio
async def test_config_get():
    async def run(i):
        key = f"TOEKN_xx{i}"
        CONFIG.set_context({"OPENAI_API_KEY": key})
        await asyncio.sleep(random.random() / 10)
        assert CONFIG.get("OPENAI_API_KEY") == key

    await asyncio.wait([run(i) for i in range(4)])
