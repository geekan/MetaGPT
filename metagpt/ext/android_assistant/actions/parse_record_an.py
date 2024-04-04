#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the ActionNode to parse record

from metagpt.actions.action_node import ActionNode

OBSERVATION = ActionNode(
    key="Observation",
    expected_type=str,
    instruction="Provide a description of your observations of the two images. "
    "Subsequently, delineate the distinctions between the first image and the second one.",
    example="",
)

THOUGHT = ActionNode(
    key="Thought",
    expected_type=str,
    instruction="Consider the impact of Action acting on UI elements.",
    example="",
)

DESCRIPTION = ActionNode(
    key="Description",
    expected_type=str,
    instruction="Describe the functionality of the UI element concisely in one or two sentences Do not include "
    "the numeric tag in your description",
    example="",
)

NODES = [OBSERVATION, THOUGHT, DESCRIPTION]

RECORD_PARSE_NODE = ActionNode.from_children("RecordParse", NODES)
