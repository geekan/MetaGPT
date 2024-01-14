#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : rebuild_sequence_view_an.py
"""
from metagpt.actions.action_node import ActionNode
from metagpt.utils.mermaid import MMC2

CODE_2_MERMAID_SEQUENCE_DIAGRAM = ActionNode(
    key="Program call flow",
    expected_type=str,
    instruction='Translate the "context" content into "format example" format.',
    example=MMC2,
)
