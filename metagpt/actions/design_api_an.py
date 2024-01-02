#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/12 22:24
@Author  : alexanderwu
@File    : design_api_an.py
"""
from typing import List

from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger
from metagpt.utils.mermaid import MMC1, MMC1_INC_AND_REFINE, MMC2, MMC2_INC

IMPLEMENTATION_APPROACH = ActionNode(
    key="Implementation approach",
    expected_type=str,
    instruction="Analyze the difficult points of the requirements, select the appropriate open-source framework",
    example="We will ...",
)

INC_IMPLEMENTATION_APPROACH = ActionNode(
    key="Incremental Implementation approach",
    expected_type=str,
    instruction="Analyze the challenging aspects of the requirements and select a suitable open-source framework. "
    "Outline the incremental steps involved in the implementation process with a list of detailed strategies.",
    example="we will ...",
)

REFINE_IMPLEMENTATION_APPROACH = ActionNode(
    key="Implementation Approach",
    expected_type=str,
    instruction="Update and extend the original implementation approach to reflect the evolving challenges and requirements "
    "due to incremental development. Provide detailed strategies for incremental steps in the implementation process."
    "etain any content unrelated to incremental development for coherence and clarity.",
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

REFINE_FILE_LIST = ActionNode(
    key="File List",
    expected_type=List[str],
    instruction="Update and expand the original file list, including only relative paths. "
    "Ensure that the refined file list reflects the evolving structure of the project due to incremental development."
    "Only output filename!Do not include comments in the list.",
    example=["main.py", "game.py", "utils.py", "new_feature.py"],
)

DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="Data structures and interfaces",
    expected_type=str,
    instruction="Use mermaid classDiagram code syntax, including classes, method(__init__ etc.) and functions with type"
    " annotations, CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. "
    "The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design.",
    example=MMC1,
)

INC_DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="Incremental Data structures and interfaces",
    expected_type=str,
    instruction="Extend the existing mermaid classDiagram code syntax to incorporate new classes, "
    "methods (including __init__), and functions with precise type annotations. Clearly delineate additional "
    "relationships between classes, maintaining adherence to PEP8 standards. Enhance the level of detail in data "
    "structures, ensuring a comprehensive API design that seamlessly integrates with the existing structure.",
    example=MMC1_INC_AND_REFINE,
)

REFINE_DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="Data Structures and Interfaces",
    expected_type=str,
    instruction="Update and extend the existing mermaid classDiagram code syntax to incorporate new classes, "
    "methods (including __init__), and functions with precise type annotations. Delineate additional "
    "relationships between classes, ensuring clarity and adherence to PEP8 standards. Further enhance the "
    "detail in data structures for a comprehensive API design that seamlessly integrates with the evolving structure."
    "Retain any content unrelated to incremental development for coherence and clarity.",
    example=MMC1_INC_AND_REFINE,
)

PROGRAM_CALL_FLOW = ActionNode(
    key="Program call flow",
    expected_type=str,
    instruction="Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE "
    "accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.",
    example=MMC2,
)

REFINE_PROGRAM_CALL_FLOW = ActionNode(
    key="Program call flow",
    expected_type=str,
    instruction="Extend the existing sequenceDiagram code syntax with detailed information, accurately covering the"
    "CRUD and initialization of each object. Ensure correct syntax usage and reflect the incremental changes introduced"
    "in the classes and API defined above.Retain content unrelated to incremental development for coherence and clarity",
    example=MMC2_INC,
)

ANYTHING_UNCLEAR = ActionNode(
    key="Anything UNCLEAR",
    expected_type=str,
    instruction="Mention unclear project aspects, then try to clarify it.",
    example="Clarification needed on third-party API integration, ...",
)

INC_DESIGN_CONTEXT = """
### Legacy Content
{old_design}

### New Requirements
{requirements}

### PRD Increment Content
{prd_increment}
"""

REFINE_DESIGN_CONTEXT = """
Role: You are a professional Architect tasked with overseeing incremental development. 
Based on new requirements, review and refine the system design. Integrate existing architecture with incremental design changes, ensuring the refined design encompasses all architectural elements, enhancements, and adjustments. Retain content unrelated to incremental development needs for coherence and clarity.

### New Requirements
{requirements}

### Legacy Content
{old_design}

### Design Increment Content
{design_increment}
"""

NODES = [
    IMPLEMENTATION_APPROACH,
    # PROJECT_NAME,
    FILE_LIST,
    DATA_STRUCTURES_AND_INTERFACES,
    PROGRAM_CALL_FLOW,
    ANYTHING_UNCLEAR,
]

INC_NODES = [INC_IMPLEMENTATION_APPROACH, INC_DATA_STRUCTURES_AND_INTERFACES, REFINE_PROGRAM_CALL_FLOW]

REFINE_NODES = [
    REFINE_IMPLEMENTATION_APPROACH,
    # PROJECT_NAME,
    REFINE_FILE_LIST,
    REFINE_DATA_STRUCTURES_AND_INTERFACES,
    REFINE_PROGRAM_CALL_FLOW,
    ANYTHING_UNCLEAR,
]

DESIGN_API_NODE = ActionNode.from_children("DesignAPI", NODES)
INC_DESIGN_NODES = ActionNode.from_children("Incremental Design API", INC_NODES)
REFINE_DESIGN_NODES = ActionNode.from_children("Refine Design API", REFINE_NODES)


def main():
    prompt = REFINE_DESIGN_NODES.compile(context="12313")
    logger.info(prompt)


if __name__ == "__main__":
    main()
