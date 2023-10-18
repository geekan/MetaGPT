#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/30 10:09
@Author  : alexanderwu
@File    : decompose.py
"""

DECOMPOSE_SYSTEM = """SYSTEM:
You serve as an assistant that helps me play Minecraft.
I will give you my goal in the game, please break it down as a tree-structure plan to achieve this goal.
The requirements of the tree-structure plan are:
1. The plan tree should be exactly of depth 2.
2. Describe each step in one line.
3. You should index the two levels like ’1.’, ’1.1.’, ’1.2.’, ’2.’, ’2.1.’, etc.
4. The sub-goals at the bottom level should be basic actions so that I can easily execute them in the game.
"""


DECOMPOSE_USER = """USER:
The goal is to {goal description}. Generate the plan according to the requirements.
"""
