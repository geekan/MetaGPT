#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/14 15:28
@Author  : alexanderwu
@File    : project_management_an.py
"""
from typing import List

from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger

REQUIRED_PYTHON_PACKAGES = ActionNode(
    key="Required Python packages",
    expected_type=List[str],
    instruction="Provide required Python packages in requirements.txt format.",
    example=["flask==1.1.2", "bcrypt==3.2.0"],
)

REQUIRED_OTHER_LANGUAGE_PACKAGES = ActionNode(
    key="Required Other language third-party packages",
    expected_type=List[str],
    instruction="List down the required packages for languages other than Python.",
    example=["No third-party dependencies required"],
)

LOGIC_ANALYSIS = ActionNode(
    key="Logic Analysis",
    expected_type=List[List[str]],
    instruction="Provide a list of files with the classes/methods/functions to be implemented, "
    "including dependency analysis and imports.",
    example=[
        ["game.py", "Contains Game class and ... functions"],
        ["main.py", "Contains main function, from game import Game"],
    ],
)

TASK_LIST = ActionNode(
    key="Task list",
    expected_type=List[str],
    instruction="Break down the tasks into a list of filenames, prioritized by dependency order.",
    example=["game.py", "main.py"],
)

FULL_API_SPEC = ActionNode(
    key="Full API spec",
    expected_type=str,
    instruction="Describe all APIs using OpenAPI 3.0 spec that may be used by both frontend and backend. If front-end "
    "and back-end communication is not required, leave it blank.",
    example="openapi: 3.0.0 ...",
)

SHARED_KNOWLEDGE = ActionNode(
    key="Shared Knowledge",
    expected_type=str,
    instruction="Detail any shared knowledge, like common utility functions or configuration variables.",
    example="'game.py' contains functions shared across the project.",
)

ANYTHING_UNCLEAR_PM = ActionNode(
    key="Anything UNCLEAR",
    expected_type=str,
    instruction="Mention any unclear aspects in the project management context and try to clarify them.",
    example="Clarification needed on how to start and initialize third-party libraries.",
)

NODES = [
    REQUIRED_PYTHON_PACKAGES,
    REQUIRED_OTHER_LANGUAGE_PACKAGES,
    LOGIC_ANALYSIS,
    TASK_LIST,
    FULL_API_SPEC,
    SHARED_KNOWLEDGE,
    ANYTHING_UNCLEAR_PM,
]


PM_NODE = ActionNode.from_children("PM_NODE", NODES)


def main():
    prompt = PM_NODE.compile(context="")
    logger.info(prompt)


if __name__ == "__main__":
    main()
