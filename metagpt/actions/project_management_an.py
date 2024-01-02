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

INCREMENTAL_LOGIC_ANALYSIS = ActionNode(
    key="Incremental Logic Analysis",
    expected_type=List[List[str]],
    instruction="Provide a list of files with the classes/methods/functions to be implemented or modified "
    "incrementally. Include thorough dependency analysis, consider potential impacts on existing code, and document"
    " necessary imports.",
    example=[
        ["new_feature.py", "Introduces NewFeature class and related functions"],
        ["utils.py", "Modifies existing utility functions to support incremental changes"],
    ],
)

REFINED_LOGIC_ANALYSIS = ActionNode(
    key="Refined Logic Analysis",
    expected_type=List[List[str]],
    instruction="Review and refine the logic analysis by merging the Legacy Content and Incremental Content. "
    "Provide a comprehensive list of files with classes/methods/functions to be implemented or modified incrementally. "
    "Include thorough dependency analysis, consider potential impacts on existing code, and document necessary imports."
    "Retain any content unrelated to incremental development for coherence and clarity.",
    example=[
        ["game.py", "Contains Game class and ... functions"],
        ["main.py", "Contains main function, from game import Game"],
        ["new_feature.py", "Introduces NewFeature class and related functions"],
        ["utils.py", "Modifies existing utility functions to support incremental changes"],
    ],
)

TASK_LIST = ActionNode(
    key="Task list",
    expected_type=List[str],
    instruction="Break down the tasks into a list of filenames, prioritized by dependency order.",
    example=["game.py", "main.py"],
)

INCREMENTAL_TASK_LIST = ActionNode(
    key="Incremental Task list",
    expected_type=List[str],
    instruction="Break down the incremental development tasks into a prioritized list of filenames."
    "Organize the tasks based on dependency order, ensuring a systematic and efficient implementation."
    "Only output filename! Do not include comments in the list ",
    example=["new_feature.py", "utils.py", "main.py"],
)

REFINED_TASK_LIST = ActionNode(
    key="Refined Task list",
    expected_type=List[str],
    instruction="Review and refine the combined task list after the merger of Legacy Content and Incremental Content. "
    "Ensure that tasks are organized in a logical and prioritized order, considering dependencies for a streamlined and"
    " efficient development process. Only output filename! Do not include comments in the list",
    example=["game.py", "utils.py", "new_feature.py", "main.py"],
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
    example="`game.py` contains functions shared across the project.",
)

INCREMENTAL_SHARED_KNOWLEDGE = ActionNode(
    key="Incremental Shared Knowledge",
    expected_type=str,
    instruction="Document any new shared knowledge generated during incremental development. This includes common "
    "utility functions, configuration variables, or any information vital for team collaboration.",
    example="`new_module.py` introduces shared utility functions for improved code reusability.",
)

REFINED_SHARED_KNOWLEDGE = ActionNode(
    key="Refined Shared Knowledge",
    expected_type=str,
    instruction="Update and expand shared knowledge to reflect any new elements introduced during incremental "
    "development. This includes common utility functions, configuration variables, or any information vital for team "
    "collaboration. Retain any content unrelated to incremental development for coherence and clarity.",
    example="`new_module.py` enhances shared utility functions for improved code reusability and collaboration.",
)


ANYTHING_UNCLEAR_PM = ActionNode(
    key="Anything UNCLEAR",
    expected_type=str,
    instruction="Mention any unclear aspects in the project management context and try to clarify them.",
    example="Clarification needed on how to start and initialize third-party libraries.",
)

INC_PM_CONTEXT = """
### Legacy Content
{old_tasks}

### New Requirements
{requirements}

### Design Increment Content
{design_increment}
"""

REFINE_PM_CONTEXT = """
Role: You are a professional Project Manager tasked with overseeing incremental development.
Based on New Requirements, refine the project context to account for incremental development. Ensure the context offers a comprehensive overview of the project's evolving scope, covering both legacy content and incremental content. Retain any content unrelated to incremental development.

# Context
## New Requirements
{requirements}

## Legacy Content
{old_tasks}

## Increment Content
{tasks_increment}
"""

NODES = [
    REQUIRED_PYTHON_PACKAGES,
    REQUIRED_OTHER_LANGUAGE_PACKAGES,
    LOGIC_ANALYSIS,
    TASK_LIST,
    FULL_API_SPEC,
    SHARED_KNOWLEDGE,
    ANYTHING_UNCLEAR_PM,
]

INC_NODES = [INCREMENTAL_LOGIC_ANALYSIS, INCREMENTAL_TASK_LIST, INCREMENTAL_SHARED_KNOWLEDGE]

REFINE_NODES = [
    REQUIRED_PYTHON_PACKAGES,
    REQUIRED_OTHER_LANGUAGE_PACKAGES,
    REFINED_LOGIC_ANALYSIS,
    REFINED_TASK_LIST,
    FULL_API_SPEC,
    REFINED_SHARED_KNOWLEDGE,
    ANYTHING_UNCLEAR_PM,
]

PM_NODE = ActionNode.from_children("PM_NODE", NODES)
INCREMENTAL_PM_NODES = ActionNode.from_children("Incremental_PM_NODES", INC_NODES)
REFINED_PM_NODES = ActionNode.from_children("Refined_PM_NODES", REFINE_NODES)


def main():
    prompt = PM_NODE.compile(context="")
    logger.info(prompt)


if __name__ == "__main__":
    main()
