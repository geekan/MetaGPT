#!/usr/bin/env python
# coding: utf-8
"""
@Time    : 2023/7/11 10:49
@Author  : chengmaoyu
@File    : test_action_output
"""
from typing import List, Tuple

from metagpt.actions import ActionOutput

t_dict = {"Required Python third-party packages": "\"\"\"\nflask==1.1.2\npygame==2.0.1\n\"\"\"\n",
          "Required Other language third-party packages": "\"\"\"\nNo third-party packages required for other languages.\n\"\"\"\n",
          "Full API spec": "\"\"\"\nopenapi: 3.0.0\ninfo:\n  title: Web Snake Game API\n  version: 1.0.0\npaths:\n  /game:\n    get:\n      summary: Get the current game state\n      responses:\n        '200':\n          description: A JSON object of the game state\n    post:\n      summary: Send a command to the game\n      requestBody:\n        required: true\n        content:\n          application/json:\n            schema:\n              type: object\n              properties:\n                command:\n                  type: string\n      responses:\n        '200':\n          description: A JSON object of the updated game state\n\"\"\"\n",
          "Logic Analysis": [
              ["app.py", "Main entry point for the Flask application. Handles HTTP requests and responses."],
              ["game.py", "Contains the Game and Snake classes. Handles the game logic."],
              ["static/js/script.js", "Handles user interactions and updates the game UI."],
              ["static/css/styles.css", "Defines the styles for the game UI."],
              ["templates/index.html", "The main page of the web application. Displays the game UI."]],
          "Task list": ["game.py", "app.py", "static/css/styles.css", "static/js/script.js", "templates/index.html"],
          "Shared Knowledge": "\"\"\"\n'game.py' contains the Game and Snake classes which are responsible for the game logic. The Game class uses an instance of the Snake class.\n\n'app.py' is the main entry point for the Flask application. It creates an instance of the Game class and handles HTTP requests and responses.\n\n'static/js/script.js' is responsible for handling user interactions and updating the game UI based on the game state returned by 'app.py'.\n\n'static/css/styles.css' defines the styles for the game UI.\n\n'templates/index.html' is the main page of the web application. It displays the game UI and loads 'static/js/script.js' and 'static/css/styles.css'.\n\"\"\"\n",
          "Anything UNCLEAR": "We need clarification on how the high score should be stored. Should it persist across sessions (stored in a database or a file) or should it reset every time the game is restarted? Also, should the game speed increase as the snake grows, or should it remain constant throughout the game?"}

WRITE_TASKS_OUTPUT_MAPPING = {
    "Required Python third-party packages": (str, ...),
    "Required Other language third-party packages": (str, ...),
    "Full API spec": (str, ...),
    "Logic Analysis": (List[Tuple[str, str]], ...),
    "Task list": (List[str], ...),
    "Shared Knowledge": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


def test_create_model_class():
    test_class = ActionOutput.create_model_class("test_class", WRITE_TASKS_OUTPUT_MAPPING)
    assert test_class.__name__ == "test_class"


def test_create_model_class_with_mapping():
    t = ActionOutput.create_model_class("test_class_1", WRITE_TASKS_OUTPUT_MAPPING)
    t1 = t(**t_dict)
    value = t1.dict()["Task list"]
    assert value == ["game.py", "app.py", "static/css/styles.css", "static/js/script.js", "templates/index.html"]


if __name__ == '__main__':
    test_create_model_class()
    test_create_model_class_with_mapping()
