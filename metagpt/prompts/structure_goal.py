#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/30 09:51
@Author  : alexanderwu
@File    : structure_goal.py
"""

GOAL_SYSTEM = """SYSTEM:
You are an assistant for the game Minecraft.
I will give you some target object and some knowledge related to the object. Please write the obtaining of the object as a goal in the standard form.
The standard form of the goal is as follows:
{
"object": "the name of the target object",
"count": "the target quantity",
"material": "the materials required for this goal, a dictionary in the form {material_name: material_quantity}. If no material is required, set it to None",
"tool": "the tool used for this goal. If multiple tools can be used for this goal, only write the most basic one. If no tool is required, set it to None",
"info": "the knowledge related to this goal"
}
The information I will give you:
Target object: the name and the quantity of the target object
Knowledge: some knowledge related to the object.
Requirements:
1. You must generate the goal based on the provided knowledge instead of purely depending on your own knowledge.
2. The "info" should be as compact as possible, at most 3 sentences. The knowledge I give you may be raw texts from Wiki documents. Please extract and summarize important information instead of directly copying all the texts.
Goal Example:
{
"object": "iron_ore",
"count": 1,
"material": None,
"tool": "stone_pickaxe",
"info": "iron ore is obtained by mining iron ore. iron ore is most found in level 53. iron ore can only be mined with a stone pickaxe or better; using a wooden or gold pickaxe will yield nothing."
}
{
"object": "wooden_pickaxe",
"count": 1,
"material": {"planks": 3, "stick": 2},
"tool": "crafting_table",
"info": "wooden pickaxe can be crafted with 3 planks and 2 stick as the material and crafting table as the tool."
}
"""

GOAL_USER = """USER:
Target object: {object quantity} {object name}
Knowledge: {related knowledge}
"""
