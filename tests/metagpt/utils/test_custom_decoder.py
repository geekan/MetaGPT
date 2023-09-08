#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/8 11:38
@Author  : femto Zheng
@File    : test_custom_decoder.py
"""


from metagpt.utils.custom_decoder import CustomDecoder


def test_parse_single_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = """{'a"
    b':'"title": "Reach and engagement of campaigns",
            "x-axis": "Low Reach --> High Reach",
            "y-axis": "Low Engagement --> High Engagement",
            "quadrant-1": "We should expand",
            "quadrant-2": "Need to promote",
            "quadrant-3": "Re-evaluate",
            "quadrant-4": "May be improved",
            "Campaign: A": [0.3, 0.6],
            "Campaign B": [0.45, 0.23],
            "Campaign C": [0.57, 0.69],
            "Campaign D": [0.78, 0.34],
            "Campaign E": [0.40, 0.34],
            "Campaign F": [0.35, 0.78],
            "Our Target Product": [0.5, 0.6]
            '
        }
    """
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert 'a"\n    b' in parsed_data


def test_parse_triple_double_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = '{"""a""":"b"}'
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert "a" in parsed_data

    input_data = '{"""a""":"""b"""}'
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "b"


def test_parse_triple_single_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = "{'''a''':'b'}"
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert "a" in parsed_data

    input_data = "{'''a''':'''b'''}"
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "b"


# def test_parse_complex():
#     # Create a custom JSON decoder
#     decoder = CustomDecoder(strict=False)
#     # Your provided input with single-quoted strings and line breaks
#     input_data = '''{
# "Required Python third-party packages": [
# "flask==1.1.2",
# "bcrypt==3.2.0"
# ],
# "Required Other language third-party packages": [
# "No third-party packages are required."
# ],
# "Full API spec": """
# openapi: 3.0.0
#
# description: A JSON object representing the game state.
#
# paths:
#   /game:
#     get:
#       summary: Get the current game state.
#       responses:
#         '200':
#           description: The current game state.
#
#   /game/{direction}:
#     post:
#       summary: Move the snake in the specified direction.
#       parameters:
#         - name: direction
#           in: path
#           description: The direction to move the snake (one of UP, DOWN, LEFT, or RIGHT).
#       responses:
#         '200':
#           description: The updated game state.
#
#   /game/{food}:
#     get:
#       summary: Get the current food position.
#       responses:
#         '200':
#           description: The current food position.
#
#   /game/{snake}:
#     get:
#       summary: Get the current snake position.
#       responses:
#         '200':
#           description: The current snake position.
#
#   /game/{snake}/{direction}:
#     post:
#       summary: Set the snake direction.
#       parameters:
#         - name: direction
#           in: path
#           description: The direction to move the snake (one of UP, DOWN, LEFT, or RIGHT).
#       responses:
#         '200':
#           description: The updated game state.
#
#   /game/end:
#     post:
#       summary: End the game.
#       responses:
#         '200':
#           description: The final game state.
# "
# ],
# "Logic Analysis": [
# ["game.py","Contains the game logic and snake movement."],
# ["snake.py","Contains the snake class and methods."],
# ["game_objects.py","Contains the game objects and their properties."],
# ["game_logic.py","Contains the game logic and rules."],
# ["ui.py","Contains the user interface and display logic."]
# ],
# "Task list": [
# "game.py",
# "snake.py",
# "game_objects.py",
# "game_logic.py",
# "ui.py"
# ],
# "Shared Knowledge": """
# The game state is represented by a JSON object.
# The snake movement is based on the direction parameter.
# The game ends when the snake collides with the wall or eats the food.
# """,
# "Anything UNCLEAR": "The requirement is clear to me."
# }
# '''
#     # Parse the JSON using the custom decoder
#
#     parsed_data = decoder.decode(input_data)
