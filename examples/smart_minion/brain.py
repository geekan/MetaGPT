#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:29
@Author  : femto Zheng
@File    : brain.py
"""
import asyncio

from metagpt.minion.brain import Brain


async def smart_brain():
    brain = Brain()

    obs, score, *_ = await brain.step(query="what's the solution for  game of 24 for 4 3 9 8")
    print(obs)

    obs, score, *_ = await brain.step(query="what's the solution for  game of 24 for 2 5 11 8")
    print(obs)
    obs, score, *_ = await brain.step(query="solve x=1/(1-beta^2*x) where beta=0.85")
    print(obs)

    obs, score, *_ = await brain.step(
        query="Write a 500000 characters novel named 'Reborn in Skyrim'. "
        "Fill the empty nodes with your own ideas. Be creative! Use your own words!"
        "I will tip you $100,000 if you write a good novel."
        "since the novel is very long, you may need to divide into subtasks"
    )
    print(obs)

    obs, score, *_ = await brain.step(
        query="""
        2024阿里巴巴全球数学竞赛

    问题1

    几位同学假期组成一个小组去某市旅游．该市有6座塔，它们的位置分别为A，B，C，D，B，F。

    同学们自由行动一段时间后，每位同学都发现，自己在所在的位置只能看到位于A，B，C，D 处的四座塔，而看不到位于E 和F的塔。已知

    (1）同学们的位置和塔的位置均视为同一平面上的点，且这些点彼此不重合：

    (2) A，B，C，D，E，F中任意3点不共线：

    (3） 看不到塔的唯一可能就是视线被其它的塔所阻挡，例如，如果某位同学所在的位置P 和A，B 共线，且A 在线段PB上，那么该同学就看不到位于B 处的塔。

    请问，这个旅游小组最多可能有多少名同学？

    (A)3 (B) 4 (C)6 (D) 12
        """
    )
    print(obs)


asyncio.run(smart_brain())
