#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the ActionNode to parse Reflection

from metagpt.actions.action_node import ActionNode

DECISION = ActionNode(
    key="Decision", expected_type=str, instruction="explain why you made this decision", example="BACK"
)


THOUGHT = ActionNode(key="Thought", expected_type=str, instruction="explain why you made this decision", example="")


DOCUMENTATION = ActionNode(
    key="Documentation", expected_type=str, instruction="describe the function of the UI element", example=""
)


NODES = [DECISION, THOUGHT, DOCUMENTATION]
SELF_LEARN_REFLECT_NODE = ActionNode.from_children("SelfLearnReflect", NODES)
