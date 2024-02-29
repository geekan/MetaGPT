#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/12 22:24
@Author  : alexanderwu
@File    : design_api_an.py
"""
from typing import List

from metagpt.actions.action_node import ActionNode
from metagpt.utils.mermaid import MMC1, MMC2

IMPLEMENTATION_APPROACH = ActionNode(
    key="Implementation approach",
    expected_type=str,
    instruction="Analyze the difficult points of the requirements, select the appropriate open-source framework",
    example="We will ...",
)

REFINED_IMPLEMENTATION_APPROACH = ActionNode(
    key="Refined Implementation Approach",
    expected_type=str,
    instruction="Update and extend the original implementation approach to reflect the evolving challenges and "
    "requirements due to incremental development. Outline the steps involved in the implementation process with the "
    "detailed strategies.",
    example="We will refine ...",
)

PROJECT_NAME = ActionNode(
    key="Project name", expected_type=str, instruction="The project name with underline", example="game_2048"
)

FILE_LIST = ActionNode(
    key="File list",
    expected_type=List[str],
    instruction="Only need relative paths. ALWAYS write a main.py or app.py here",
    example=["main.py", "game.py"],
)

REFINED_FILE_LIST = ActionNode(
    key="Refined File list",
    expected_type=List[str],
    instruction="Update and expand the original file list including only relative paths. Up to 2 files can be added."
    "Ensure that the refined file list reflects the evolving structure of the project.",
    example=["main.py", "game.py", "new_feature.py"],
)

DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="Data structures and interfaces",
    expected_type=str,
    instruction="Use mermaid classDiagram code syntax, including classes, method(__init__ etc.) and functions with type"
    " annotations, CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. "
    "The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design.",
    example=MMC1,
)

REFINED_DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="Refined Data structures and interfaces",
    expected_type=str,
    instruction="Update and extend the existing mermaid classDiagram code syntax to incorporate new classes, "
    "methods (including __init__), and functions with precise type annotations. Delineate additional "
    "relationships between classes, ensuring clarity and adherence to PEP8 standards."
    "Retain content that is not related to incremental development but important for consistency and clarity.",
    example=MMC1,
)

PROGRAM_CALL_FLOW = ActionNode(
    key="Program call flow",
    expected_type=str,
    instruction="Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE "
    "accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.",
    example=MMC2,
)

REFINED_PROGRAM_CALL_FLOW = ActionNode(
    key="Refined Program call flow",
    expected_type=str,
    instruction="Extend the existing sequenceDiagram code syntax with detailed information, accurately covering the"
    "CRUD and initialization of each object. Ensure correct syntax usage and reflect the incremental changes introduced"
    "in the classes and API defined above. "
    "Retain content that is not related to incremental development but important for consistency and clarity.",
    example=MMC2,
)

ANYTHING_UNCLEAR = ActionNode(
    key="Anything UNCLEAR",
    expected_type=str,
    instruction="Mention unclear project aspects, then try to clarify it.",
    example="Clarification needed on third-party API integration, ...",
)

NODES = [
    IMPLEMENTATION_APPROACH,
    # PROJECT_NAME,
    FILE_LIST,
    DATA_STRUCTURES_AND_INTERFACES,
    PROGRAM_CALL_FLOW,
    ANYTHING_UNCLEAR,
]

REFINED_NODES = [
    REFINED_IMPLEMENTATION_APPROACH,
    REFINED_FILE_LIST,
    REFINED_DATA_STRUCTURES_AND_INTERFACES,
    REFINED_PROGRAM_CALL_FLOW,
    ANYTHING_UNCLEAR,
]

DESIGN_API_NODE = ActionNode.from_children("DesignAPI", NODES)
REFINED_DESIGN_NODE = ActionNode.from_children("RefinedDesignAPI", REFINED_NODES)
