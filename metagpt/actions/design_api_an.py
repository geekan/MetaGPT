#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/12 22:24
@Author  : alexanderwu
@File    : design_api_an.py
"""
from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger

IMPLEMENTATION_APPROACH = ActionNode(
    key="Implementation approach",
    expected_type=str,
    instruction="Analyze the difficult points of the requirements, select the appropriate open-source framework",
    example="We will ..."
)

PROJECT_NAME = ActionNode(
    key="Project name",
    expected_type=str,
    instruction="The project name with underline",
    example="game_2048"
)

FILE_LIST = ActionNode(
    key="File list",
    expected_type=list[str],
    instruction="Only need relative paths. ALWAYS write a main.py or app.py here",
    example=['main.py', 'game.py']
)

DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="Data structures and interfaces",
    expected_type=str,
    instruction="Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions "
                "(with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. "
                "The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design.",
    example="""    classDiagram
        class User {
            +int id
            +str username
            +str email
            +str password
            __init__(id: int, username: str, email: str, password: str)
            follow(user: User): void
            like(content: Content): void
            comment(content: Content, text: str): Comment
        }
        class Content {
            +int id
            +User author
            +str title
            +str body
            +datetime created_at
            +list likes
            +list comments
            __init__(id: int, author: User, title: str, body: str)
            get_likes(): list
            get_comments(): list
        }
        class Comment {
            +int id
            +User author
            +str text
            +datetime created_at
            __init__(id: int, author: User, text: str)
        }
        class Leaderboard {
            +list top_contents
            update(): void
        }
        class SearchEngine {
            +str query
            search(): list
        }
        class RecommendationEngine {
            +User user
            recommend(): list
        }
        class TaskQueue {
            +str task_name
            enqueue(task: function): void
        }
        User "1" -- "*" Content: creates
        Content "1" -- "*" Comment: includes
        User "1" -- "*" Comment: writes
        User "1" -- "*" User: follows
        Content "1" -- "*" User: liked_by"""
)

PROGRAM_CALL_FLOW = ActionNode(
    key="Program call flow",
    expected_type=str,
    instruction="Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE "
                "accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.",
    example="""sequenceDiagram
participant M as Main
...
G->>M: end game"""
)

ANYTHING_UNCLEAR = ActionNode(
    key="Anything UNCLEAR",
    expected_type=str,
    instruction="Mention unclear project aspects, then try to clarify it.",
    example="Clarification needed on third-party API integration, ..."
)

ACTION_NODES = [
    IMPLEMENTATION_APPROACH,
    PROJECT_NAME,
    FILE_LIST,
    DATA_STRUCTURES_AND_INTERFACES,
    PROGRAM_CALL_FLOW,
    ANYTHING_UNCLEAR
]

DESIGN_API_NODE = ActionNode("DesignAPI", str, "", "")
DESIGN_API_NODE.add_children(ACTION_NODES)

SIMPLE_TEMPLATE = """
## context
{context}

## example
{example}

## instruction-nodes: "<node>: <type>  # <comment>"
{instruction}

## instruction-action
Role: You are an architect; the goal is to design a SOTA software system
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
Requirement: Fill in the above missing instruction-nodes based on the context
now, output wrapped inside [CONTENT][/CONTENT] as example, nothing else.
"""


def main():
    instruction, example = DESIGN_API_NODE.compile()
    text = SIMPLE_TEMPLATE.format(context="", example=example, instruction=instruction)
    logger.info(text)


if __name__ == '__main__':
    main()
