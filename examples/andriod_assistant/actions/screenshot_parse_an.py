#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the ActionNode to parse screenshot

from metagpt.actions.action_node import ActionNode

OBSERVATION = ActionNode(
    key="Observation", expected_type=str, instruction="Describe what you observe in the image", example=""
)

THOUGHT = ActionNode(
    key="Thought",
    expected_type=str,
    instruction="To complete the given task, what is the next step I should do",
    example="",
)

ACTION = ActionNode(
    key="Action",
    expected_type=str,
    instruction="The function call with the correct parameters to proceed with the task. If you believe the task is "
    "completed or there is nothing to be done, you should output FINISH. You cannot output anything else "
    "except a function call or FINISH in this field.",
    example="",
)

SUMMARY = ActionNode(
    key="Summary",
    expected_type=str,
    instruction="Summarize your past actions along with your latest action in one or two sentences. Do not include "
    "the numeric tag in your summary",
    example="",
)

SUMMARY_GRID = ActionNode(
    key="Summary",
    expected_type=str,
    instruction="Summarize your past actions along with your latest action in one or two sentences. Do not include "
    "the grid area number in your summary",
    example="",
)

NODES = [OBSERVATION, THOUGHT, ACTION, SUMMARY]

NODES_GRID = [OBSERVATION, THOUGHT, ACTION, SUMMARY_GRID]

SCREENSHOT_PARSE_NODE = ActionNode.from_children("ScreenshotParse", NODES)
SCREENSHOT_PARSE_GRID_NODE = ActionNode.from_children("ScreenshotParseGrid", NODES_GRID)
