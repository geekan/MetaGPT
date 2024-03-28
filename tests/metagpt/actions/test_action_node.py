#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/23 15:49
@Author  : alexanderwu
@File    : test_action_node.py
"""
from pathlib import Path
from typing import List, Tuple

import pytest
from pydantic import BaseModel, Field, ValidationError

from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode, ReviewMode, ReviseMode
from metagpt.environment import Environment
from metagpt.llm import LLM
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team
from metagpt.utils.common import encode_image


@pytest.mark.asyncio
async def test_debate_two_roles():
    action1 = Action(name="AlexSay", instruction="Express your opinion with emotion and don't repeat it")
    action2 = Action(name="BobSay", instruction="Express your opinion with emotion and don't repeat it")
    alex = Role(
        name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action1], watch=[action2]
    )
    bob = Role(name="Bob", profile="Republican candidate", goal="Win the election", actions=[action2], watch=[action1])
    env = Environment(desc="US election live broadcast")
    team = Team(investment=10.0, env=env, roles=[alex, bob])

    history = await team.run(idea="Topic: climate change. Under 80 words per message.", send_to="Alex", n_round=3)
    assert "Alex" in history


@pytest.mark.asyncio
async def test_debate_one_role_in_env():
    action = Action(name="Debate", instruction="Express your opinion with emotion and don't repeat it")
    alex = Role(name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action])
    env = Environment(desc="US election live broadcast")
    team = Team(investment=10.0, env=env, roles=[alex])
    history = await team.run(idea="Topic: climate change. Under 80 words per message.", send_to="Alex", n_round=3)
    assert "Alex" in history


@pytest.mark.asyncio
async def test_debate_one_role():
    action = Action(name="Debate", instruction="Express your opinion with emotion and don't repeat it")
    alex = Role(name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action])
    msg: Message = await alex.run("Topic: climate change. Under 80 words per message.")

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


@pytest.mark.asyncio
async def test_action_node_review():
    key = "Project Name"
    node_a = ActionNode(
        key=key,
        expected_type=str,
        instruction='According to the content of "Original Requirements," name the project using snake case style '
        "with underline, like 'game_2048' or 'simple_crm.",
        example="game_2048",
    )

    with pytest.raises(RuntimeError):
        _ = await node_a.review()

    _ = await node_a.fill(context=None, llm=LLM())
    setattr(node_a.instruct_content, key, "game snake")  # wrong content to review

    review_comments = await node_a.review(review_mode=ReviewMode.AUTO)
    assert len(review_comments) == 1
    assert list(review_comments.keys())[0] == key

    review_comments = await node_a.review(strgy="complex", review_mode=ReviewMode.AUTO)
    assert len(review_comments) == 0

    node = ActionNode.from_children(key="WritePRD", nodes=[node_a])
    with pytest.raises(RuntimeError):
        _ = await node.review()

    _ = await node.fill(context=None, llm=LLM())

    review_comments = await node.review(review_mode=ReviewMode.AUTO)
    assert len(review_comments) == 1
    assert list(review_comments.keys())[0] == key

    review_comments = await node.review(strgy="complex", review_mode=ReviewMode.AUTO)
    assert len(review_comments) == 1
    assert list(review_comments.keys())[0] == key


@pytest.mark.asyncio
async def test_action_node_revise():
    key = "Project Name"
    node_a = ActionNode(
        key=key,
        expected_type=str,
        instruction='According to the content of "Original Requirements," name the project using snake case style '
        "with underline, like 'game_2048' or 'simple_crm.",
        example="game_2048",
    )

    with pytest.raises(RuntimeError):
        _ = await node_a.review()

    _ = await node_a.fill(context=None, llm=LLM())
    setattr(node_a.instruct_content, key, "game snake")  # wrong content to revise
    revise_contents = await node_a.revise(revise_mode=ReviseMode.AUTO)
    assert len(revise_contents) == 1
    assert "game_snake" in getattr(node_a.instruct_content, key)

    revise_contents = await node_a.revise(strgy="complex", revise_mode=ReviseMode.AUTO)
    assert len(revise_contents) == 0

    node = ActionNode.from_children(key="WritePRD", nodes=[node_a])
    with pytest.raises(RuntimeError):
        _ = await node.revise()

    _ = await node.fill(context=None, llm=LLM())
    setattr(node.instruct_content, key, "game snake")
    revise_contents = await node.revise(revise_mode=ReviseMode.AUTO)
    assert len(revise_contents) == 1
    assert "game_snake" in getattr(node.instruct_content, key)

    revise_contents = await node.revise(strgy="complex", revise_mode=ReviseMode.AUTO)
    assert len(revise_contents) == 1
    assert "game_snake" in getattr(node.instruct_content, key)


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
    print(output.model_json_schema())
    assert output.model_json_schema()["title"] == "test_class"
    assert output.model_json_schema()["type"] == "object"
    assert output.model_json_schema()["properties"]["Full API spec"]


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


@pytest.mark.asyncio
async def test_action_node_with_image(mocker):
    # add a mock to update model in unittest, due to the gloabl MockLLM
    def _cons_kwargs(self, messages: list[dict], timeout=3, **extra_kwargs) -> dict:
        kwargs = {"messages": messages, "temperature": 0.3, "model": "gpt-4-vision-preview"}
        return kwargs

    invoice = ActionNode(
        key="invoice", expected_type=bool, instruction="if it's a invoice file, return True else False", example="False"
    )

    invoice_path = Path(__file__).parent.joinpath("..", "..", "data", "invoices", "invoice-2.png")
    img_base64 = encode_image(invoice_path)
    mocker.patch("metagpt.provider.openai_api.OpenAILLM._cons_kwargs", _cons_kwargs)
    node = await invoice.fill(context="", llm=LLM(), images=[img_base64])
    assert node.instruct_content.invoice


class ToolDef(BaseModel):
    tool_name: str = Field(default="a", description="tool name", examples=[])
    description: str = Field(default="b", description="tool description", examples=[])


class Task(BaseModel):
    task_id: int = Field(default=1, description="task id", examples=[1, 2, 3])
    name: str = Field(default="Get data from ...", description="task name", examples=[])
    dependent_task_ids: List[int] = Field(default=[], description="dependent task ids", examples=[1, 2, 3])
    tool: ToolDef = Field(default=ToolDef(), description="tool use", examples=[])


class Tasks(BaseModel):
    tasks: List[Task] = Field(default=[], description="tasks", examples=[])


def test_action_node_from_pydantic_and_print_everything():
    node = ActionNode.from_pydantic(Task)
    print("1. Tasks")
    print(Task().model_dump_json(indent=4))
    print(Tasks.model_json_schema())
    print("2. Task")
    print(Task.model_json_schema())
    print("3. ActionNode")
    print(node)
    print("4. node.compile prompt")
    prompt = node.compile(context="")
    assert "tool_name" in prompt, "tool_name should be in prompt"
    print(prompt)
    print("5. node.get_children_mapping")
    print(node._get_children_mapping())
    print("6. node.create_children_class")
    children_class = node._create_children_class()
    print(children_class)
    import inspect

    code = inspect.getsource(Tasks)
    print(code)
    assert "tasks" in code, "tasks should be in code"


if __name__ == "__main__":
    test_create_model_class()
    test_create_model_class_with_mapping()
