#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:31
@Author  : alexanderwu
@File    : test_design_api_review.py
"""
import pytest

from metagpt.actions.design_api_review import DesignReview


@pytest.mark.asyncio
async def test_design_api_review(context):
    prd = "我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。"
    api_design = """
数据结构:
1. Song: 包含歌曲信息，如标题、艺术家等。
2. Playlist: 包含一系列歌曲。

API列表:
1. play(song: Song): 开始播放指定的歌曲。
2. pause(): 暂停当前播放的歌曲。
3. next(): 跳到播放列表的下一首歌曲。
4. previous(): 跳到播放列表的上一首歌曲。
"""
    _ = "API设计看起来非常合理，满足了PRD中的所有需求。"

    design_api_review = DesignReview(context=context)

    result = await design_api_review.run(prd, api_design)

    _ = f"以下是产品需求文档(PRD):\n\n{prd}\n\n以下是基于这个PRD设计的API列表:\n\n{api_design}\n\n请审查这个API设计是否满足PRD的需求，以及是否符合良好的设计实践。"
    # mock_llm.ask.assert_called_once_with(prompt)
    assert len(result) > 0
