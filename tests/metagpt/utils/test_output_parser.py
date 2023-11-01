#!/usr/bin/env python
# coding: utf-8
"""
@Time    : 2023/7/11 10:25
@Author  : chengmaoyu
@File    : test_output_parser.py
"""
from typing import List, Tuple, Union

import pytest

from metagpt.utils.common import OutputParser


def test_parse_blocks():
    test_text = "##block1\nThis is block 1.\n##block2\nThis is block 2."
    expected_result = {'block1': 'This is block 1.', 'block2': 'This is block 2.'}
    assert OutputParser.parse_blocks(test_text) == expected_result


def test_parse_code():
    test_text = "```python\nprint('Hello, world!')```"
    expected_result = "print('Hello, world!')"
    assert OutputParser.parse_code(test_text, 'python') == expected_result

    with pytest.raises(Exception):
        OutputParser.parse_code(test_text, 'java')


def test_parse_python_code():
    expected_result = "print('Hello, world!')"
    assert OutputParser.parse_python_code("```python\nprint('Hello, world!')```") == expected_result
    assert OutputParser.parse_python_code("```python\nprint('Hello, world!')") == expected_result
    assert OutputParser.parse_python_code("print('Hello, world!')") == expected_result
    assert OutputParser.parse_python_code("print('Hello, world!')```") == expected_result
    assert OutputParser.parse_python_code("print('Hello, world!')```") == expected_result
    expected_result = "print('```Hello, world!```')"
    assert OutputParser.parse_python_code("```python\nprint('```Hello, world!```')```") == expected_result
    assert OutputParser.parse_python_code("The code is: ```python\nprint('```Hello, world!```')```") == expected_result
    assert OutputParser.parse_python_code("xxx.\n```python\nprint('```Hello, world!```')```\nxxx") == expected_result

    with pytest.raises(ValueError):
        OutputParser.parse_python_code("xxx =")


def test_parse_str():
    test_text = "name = 'Alice'"
    expected_result = 'Alice'
    assert OutputParser.parse_str(test_text) == expected_result


def test_parse_file_list():
    test_text = "files=['file1', 'file2', 'file3']"
    expected_result = ['file1', 'file2', 'file3']
    assert OutputParser.parse_file_list(test_text) == expected_result

    with pytest.raises(Exception):
        OutputParser.parse_file_list("wrong_input")


def test_parse_data():
    test_data = "##block1\n```python\nprint('Hello, world!')\n```\n##block2\nfiles=['file1', 'file2', 'file3']"
    expected_result = {'block1': "print('Hello, world!')", 'block2': ['file1', 'file2', 'file3']}
    assert OutputParser.parse_data(test_data) == expected_result


@pytest.mark.parametrize(
    ("text", "data_type", "parsed_data", "expected_exception"),
    [
        (
            """xxx [1, 2, ["a", "b", [3, 4]], {"x": 5, "y": [6, 7]}] xxx""",
            list,
            [1, 2, ["a", "b", [3, 4]], {"x": 5, "y": [6, 7]}],
            None,
        ),
        (
            """xxx ["1", "2", "3"] xxx \n xxx \t xx""",
            list,
            ["1", "2", "3"],
            None,
        ),
        (
            """{"title": "a", "directory": {"sub_dir1": ["title1, title2"]}, "sub_dir2": [1, 2]}""",
            dict,
            {"title": "a", "directory": {"sub_dir1": ["title1, title2"]}, "sub_dir2": [1, 2]},
            None,
        ),
        (
            """xxx {"title": "x", \n  \t "directory": ["x", \n "y"]} xxx \n xxx \t xx""",
            dict,
            {"title": "x", "directory": ["x", "y"]},
            None,
        ),
        (
            """xxx xx""",
            list,
            None,
            [],
        ),
        (
            """xxx [1, 2, []xx""",
            list,
            None,
            Exception,
        ),
    ]
)
def test_extract_struct(text: str, data_type: Union[type(list), type(dict)], parsed_data: Union[list, dict], expected_exception):
    def case():
        resp = OutputParser.extract_struct(text, data_type)
        assert resp == parsed_data

    if expected_exception:
        with pytest.raises(expected_exception):
            case()
    else:
        case()


if __name__ == '__main__':
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

    OUTPUT_MAPPING = {
        "Original Requirements": (str, ...),
        "Product Goals": (List[str], ...),
        "User Stories": (List[str], ...),
        "Competitive Analysis": (List[str], ...),
        "Competitive Quadrant Chart": (str, ...),
        "Requirement Analysis": (str, ...),
        "Requirement Pool": (List[Tuple[str, str]], ...),
        "Anything UNCLEAR": (str, ...),
    }
    t_text1 = '''## Original Requirements:

The boss wants to create a web-based version of the game "Fly Bird".

## Product Goals:

- Create a web-based version of the game "Fly Bird" that is engaging and addictive.
- Provide a seamless and intuitive user experience.
- Optimize the game for different devices and screen sizes.

## User Stories:

- As a user, I want to be able to control the bird's flight by clicking or tapping on the screen.
- As a user, I want to see my score and the highest score achieved in the game.
- As a user, I want the game to be challenging but not frustratingly difficult.
- As a user, I want to be able to pause and resume the game at any time.
- As a user, I want to be able to share my score on social media.

## Competitive Analysis:

- Flappy Bird: A popular mobile game where the player controls a bird's flight through a series of obstacles.
- Angry Birds: A physics-based puzzle game where the player launches birds to destroy structures and defeat pigs.
- Snake Game: A classic game where the player controls a snake to eat food and grow longer without hitting the walls or its own body.
- Temple Run: An endless running game where the player controls a character to avoid obstacles and collect coins.
- Subway Surfers: An endless running game where the player controls a character to avoid obstacles and collect coins while being chased by a guard.
- Doodle Jump: A vertical platform game where the player controls a character to jump on platforms and avoid falling.
- Fruit Ninja: A fruit-slicing game where the player uses their finger to slice flying fruits.

## Competitive Quadrant Chart:

```mermaid
quadrantChart
    title Reach and engagement of games
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 We should expand
    quadrant-2 Need to promote
    quadrant-3 Re-evaluate
    quadrant-4 May be improved
    "Flappy Bird": [0.8, 0.9]
    "Angry Birds": [0.9, 0.8]
    "Snake Game": [0.6, 0.6]
    "Temple Run": [0.9, 0.7]
    "Subway Surfers": [0.9, 0.7]
    "Doodle Jump": [0.7, 0.5]
    "Fruit Ninja": [0.8, 0.6]
    "Our Target Product": [0.7, 0.8]
```

## Requirement Analysis:

The product should be a web-based version of the game "Fly Bird" that is engaging, addictive, and optimized for different devices and screen sizes. It should provide a seamless and intuitive user experience, with controls that allow the user to control the bird's flight by clicking or tapping on the screen. The game should display the user's score and the highest score achieved. It should be challenging but not frustratingly difficult, allowing the user to pause and resume the game at any time. The user should also have the option to share their score on social media.

## Requirement Pool:

```python
[
    ("Implement bird's flight control using click or tap", "P0"),
    ("Display user's score and highest score achieved", "P0"),
    ("Implement challenging but not frustrating difficulty level", "P1"),
    ("Allow user to pause and resume the game", "P1"),
    ("Implement social media sharing feature", "P2")
]
```

## Anything UNCLEAR:

There are no unclear points.
    '''
    d = OutputParser.parse_data_with_mapping(t_text1, OUTPUT_MAPPING)
    import json

    print(json.dumps(d))
