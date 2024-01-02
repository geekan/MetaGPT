#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/23 15:49
@Author  : alexanderwu
@File    : test_action_node.py
"""
from typing import List, Tuple

import pytest
from pydantic import ValidationError

from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode
from metagpt.environment import Environment
from metagpt.llm import LLM
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team


@pytest.mark.asyncio
async def test_debate_two_roles():
    action1 = Action(name="AlexSay", instruction="Express your opinion with emotion and don't repeat it")
    action2 = Action(name="BobSay", instruction="Express your opinion with emotion and don't repeat it")
    biden = Role(
        name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action1], watch=[action2]
    )
    trump = Role(
        name="Bob", profile="Republican candidate", goal="Win the election", actions=[action2], watch=[action1]
    )
    env = Environment(desc="US election live broadcast")
    team = Team(investment=10.0, env=env, roles=[biden, trump])

    history = await team.run(idea="Topic: climate change. Under 80 words per message.", send_to="Alex", n_round=3)
    assert "Alex" in history


@pytest.mark.asyncio
async def test_debate_one_role_in_env():
    action = Action(name="Debate", instruction="Express your opinion with emotion and don't repeat it")
    biden = Role(name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action])
    env = Environment(desc="US election live broadcast")
    team = Team(investment=10.0, env=env, roles=[biden])
    history = await team.run(idea="Topic: climate change. Under 80 words per message.", send_to="Alex", n_round=3)
    assert "Alex" in history


@pytest.mark.asyncio
async def test_debate_one_role():
    action = Action(name="Debate", instruction="Express your opinion with emotion and don't repeat it")
    biden = Role(name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action])
    msg: Message = await biden.run("Topic: climate change. Under 80 words per message.")

    assert len(msg.content) > 10
    assert msg.sent_from == "metagpt.roles.role.Role"


@pytest.mark.asyncio
async def test_action_node_one_layer():
    node = ActionNode(key="key-a", expected_type=str, instruction="instruction-b", example="example-c")

    raw_template = node.compile(context="123", schema="raw", mode="auto")
    json_template = node.compile(context="123", schema="json", mode="auto")
    markdown_template = node.compile(context="123", schema="markdown", mode="auto")
    node_dict = node.to_dict()

    assert "123" in raw_template
    assert "instruction" in raw_template

    assert "123" in json_template
    assert "format example" in json_template
    assert "constraint" in json_template
    assert "action" in json_template
    assert "[/" in json_template

    assert "123" in markdown_template
    assert "key-a" in markdown_template

    assert node_dict["key-a"] == "instruction-b"
    assert "key-a" in repr(node)


@pytest.mark.asyncio
async def test_action_node_two_layer():
    node_a = ActionNode(key="reasoning", expected_type=str, instruction="reasoning step by step", example="")
    node_b = ActionNode(key="answer", expected_type=str, instruction="the final answer", example="")

    root = ActionNode.from_children(key="detail answer", nodes=[node_a, node_b])
    assert "reasoning" in root.children
    assert node_b in root.children.values()

    # FIXME: ADD MARKDOWN SUPPORT. NEED TO TUNE MARKDOWN SYMBOL FIRST.
    answer1 = await root.fill(context="what's the answer to 123+456?", schema="json", strgy="simple", llm=LLM())
    assert "579" in answer1.content

    answer2 = await root.fill(context="what's the answer to 123+456?", schema="json", strgy="complex", llm=LLM())
    assert "579" in answer2.content


t_dict = {
    "Required Python third-party packages": '"""\nflask==1.1.2\npygame==2.0.1\n"""\n',
    "Required Other language third-party packages": '"""\nNo third-party packages required for other languages.\n"""\n',
    "Full API spec": '"""\nopenapi: 3.0.0\ninfo:\n  title: Web Snake Game API\n  version: 1.0.0\npaths:\n  /game:\n    get:\n      summary: Get the current game state\n      responses:\n        \'200\':\n          description: A JSON object of the game state\n    post:\n      summary: Send a command to the game\n      requestBody:\n        required: true\n        content:\n          application/json:\n            schema:\n              type: object\n              properties:\n                command:\n                  type: string\n      responses:\n        \'200\':\n          description: A JSON object of the updated game state\n"""\n',
    "Logic Analysis": [
        ["app.py", "Main entry point for the Flask application. Handles HTTP requests and responses."],
        ["game.py", "Contains the Game and Snake classes. Handles the game logic."],
        ["static/js/script.js", "Handles user interactions and updates the game UI."],
        ["static/css/styles.css", "Defines the styles for the game UI."],
        ["templates/index.html", "The main page of the web application. Displays the game UI."],
    ],
    "Task list": ["game.py", "app.py", "static/css/styles.css", "static/js/script.js", "templates/index.html"],
    "Shared Knowledge": "\"\"\"\n'game.py' contains the Game and Snake classes which are responsible for the game logic. The Game class uses an instance of the Snake class.\n\n'app.py' is the main entry point for the Flask application. It creates an instance of the Game class and handles HTTP requests and responses.\n\n'static/js/script.js' is responsible for handling user interactions and updating the game UI based on the game state returned by 'app.py'.\n\n'static/css/styles.css' defines the styles for the game UI.\n\n'templates/index.html' is the main page of the web application. It displays the game UI and loads 'static/js/script.js' and 'static/css/styles.css'.\n\"\"\"\n",
    "Anything UNCLEAR": "We need clarification on how the high score should be stored. Should it persist across sessions (stored in a database or a file) or should it reset every time the game is restarted? Also, should the game speed increase as the snake grows, or should it remain constant throughout the game?",
}

t_dict_min = {
    "Required Python third-party packages": '"""\nflask==1.1.2\npygame==2.0.1\n"""\n',
}

WRITE_TASKS_OUTPUT_MAPPING = {
    "Required Python third-party packages": (str, ...),
    "Required Other language third-party packages": (str, ...),
    "Full API spec": (str, ...),
    "Logic Analysis": (List[Tuple[str, str]], ...),
    "Task list": (List[str], ...),
    "Shared Knowledge": (str, ...),
    "Anything UNCLEAR": (str, ...),
}

WRITE_TASKS_OUTPUT_MAPPING_MISSING = {
    "Required Python third-party packages": (str, ...),
}


def test_create_model_class():
    test_class = ActionNode.create_model_class("test_class", WRITE_TASKS_OUTPUT_MAPPING)
    assert test_class.__name__ == "test_class"

    output = test_class(**t_dict)
    print(output.schema())
    assert output.schema()["title"] == "test_class"
    assert output.schema()["type"] == "object"
    assert output.schema()["properties"]["Full API spec"]


def test_create_model_class_with_fields_unrecognized():
    test_class = ActionNode.create_model_class("test_class", WRITE_TASKS_OUTPUT_MAPPING_MISSING)
    assert test_class.__name__ == "test_class"

    _ = test_class(**t_dict)  # just warning


def test_create_model_class_with_fields_missing():
    test_class = ActionNode.create_model_class("test_class", WRITE_TASKS_OUTPUT_MAPPING)
    assert test_class.__name__ == "test_class"

    with pytest.raises(ValidationError):
        _ = test_class(**t_dict_min)


def test_create_model_class_with_mapping():
    t = ActionNode.create_model_class("test_class_1", WRITE_TASKS_OUTPUT_MAPPING)
    t1 = t(**t_dict)
    value = t1.model_dump()["Task list"]
    assert value == ["game.py", "app.py", "static/css/styles.css", "static/js/script.js", "templates/index.html"]


if __name__ == "__main__":
    test_create_model_class()
    test_create_model_class_with_mapping()
