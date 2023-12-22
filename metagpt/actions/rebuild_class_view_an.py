#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : rebuild_class_view_an.py
@Desc    : Defines `ActionNode` objects used by rebuild_class_view.py
"""
from metagpt.actions.action_node import ActionNode

CLASS_SOURCE_CODE_BLOCK = ActionNode(
    key="Class View",
    expected_type=str,
    instruction='Generate the mermaid class diagram corresponding to source code in "context."',
    example="""
    classDiagram
        class A {
        -int x
        +int y
        -int speed
        -int direction
        +__init__(x: int, y: int, speed: int, direction: int)
        +change_direction(new_direction: int) None
        +move() None
    }
    """,
)

REBUILD_CLASS_VIEW_NODES = [
    CLASS_SOURCE_CODE_BLOCK,
]

REBUILD_CLASS_VIEW_NODE = ActionNode.from_children("RebuildClassView", REBUILD_CLASS_VIEW_NODES)
