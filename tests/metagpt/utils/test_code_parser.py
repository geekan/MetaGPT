#!/usr/bin/env python
# coding: utf-8
"""
@Time    : 2023/7/10 17:14
@Author  : chengmaoyu
@File    : test_code_parser.py
"""

import pytest

from metagpt.utils.common import CodeParser

t_text = '''
## Required Python third-party packages
```python
"""
flask==1.1.2
pygame==2.0.1
"""
```

## Required Other language third-party packages
```python
"""
No third-party packages required for other languages.
"""
```

## Full API spec
```python
"""
openapi: 3.0.0
info:
  title: Web Snake Game API
  version: 1.0.0
paths:
  /game:
    get:
      summary: Get the current game state
      responses:
        '200':
          description: A JSON object of the game state
    post:
      summary: Send a command to the game
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                command:
                  type: string
      responses:
        '200':
          description: A JSON object of the updated game state
"""
```

## Logic Analysis
```python
[
    ("app.py", "Main entry point for the Flask application. Handles HTTP requests and responses."),
    ("game.py", "Contains the Game and Snake classes. Handles the game logic."),
    ("static/js/script.js", "Handles user interactions and updates the game UI."),
    ("static/css/styles.css", "Defines the styles for the game UI."),
    ("templates/index.html", "The main page of the web application. Displays the game UI.")
]
```

## Task list
```python
[
    "game.py",
    "app.py",
    "static/css/styles.css",
    "static/js/script.js",
    "templates/index.html"
]
```

## Shared Knowledge
```python
"""
'game.py' contains the Game and Snake classes which are responsible for the game logic. The Game class uses an instance of the Snake class.

'app.py' is the main entry point for the Flask application. It creates an instance of the Game class and handles HTTP requests and responses.

'static/js/script.js' is responsible for handling user interactions and updating the game UI based on the game state returned by 'app.py'.

'static/css/styles.css' defines the styles for the game UI.

'templates/index.html' is the main page of the web application. It displays the game UI and loads 'static/js/script.js' and 'static/css/styles.css'.
"""
```

## Anything UNCLEAR
We need clarification on how the high score should be stored. Should it persist across sessions (stored in a database or a file) or should it reset every time the game is restarted? Also, should the game speed increase as the snake grows, or should it remain constant throughout the game?
        '''


class TestCodeParser:
    @pytest.fixture
    def parser(self):
        return CodeParser()

    @pytest.fixture
    def text(self):
        return t_text

    def test_parse_blocks(self, parser, text):
        result = parser.parse_blocks(text)
        print(result)
        assert "game.py" in result["Task list"]

    def test_parse_block(self, parser, text):
        result = parser.parse_block("Task list", text)
        print(result)
        assert "game.py" in result

    def test_parse_code(self, parser, text):
        result = parser.parse_code("Task list", text, "python")
        print(result)
        assert "game.py" in result

    def test_parse_str(self, parser, text):
        result = parser.parse_str("Anything UNCLEAR", text, "python")
        print(result)
        assert "We need clarification on how the high score " in result

    def test_parse_file_list(self, parser, text):
        result = parser.parse_file_list("Task list", text)
        print(result)
        assert "game.py" in result


if __name__ == "__main__":
    t = TestCodeParser()
    t.test_parse_file_list(CodeParser(), t_text)
    # TestCodeParser.test_parse_file_list()
