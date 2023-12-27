#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/28
@Author  : mashenquan
@File    : test_research.py
"""

import pytest

from metagpt.actions import CollectLinks


@pytest.mark.asyncio
async def test_action():
    action = CollectLinks()
    result = await action.run(topic="baidu")
    assert result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
