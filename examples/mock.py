#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.actions import BossRequirement, WriteDesign, WritePRD, WriteTasks
from metagpt.schema import Message

BOSS_REQUIREMENT = """The boss wants a snake game that is playable and has multiple mazes."""

DETAIL_REQUIREMENT = """
## Requirement Analysis:
The product should be a playable snake game with multiple mazes to choose from. It should have basic functionality such as controlling the snake's movement, increasing the score when the snake eats food, and ending the game when the snake collides with itself or the walls. The game should also allow users to select different mazes for added variety. 

## Requirement Pool:
```python
[
    ("Control the snake's movement using arrow keys or swipe gestures on mobile devices", "P0"),
    ("Increase the score when the snake eats food and grows longer", "P0"),
    ("End the game when the snake collides with itself or the walls", "P0"),
    ("Allow users to select different mazes to play in", "P1"),
    ("Allow users to pause the game and resume playing later", "P1")
]
```

## UI Design draft:
The game will have a grid-based layout where the snake and food will be represented by different colored squares. The player will control the snake's movement using arrow keys or swipe gestures on mobile devices. The score will be displayed on the screen and will increase as the snake eats food. There will be buttons to pause the game and restart it. The game will also have a menu where the player can select different mazes to play in.
"""


PRD = '''
## Original Requirements:
The boss wants to create a snake game that is playable and has multiple mazes.

## Product Goals:
- Create a playable snake game
- Include multiple mazes for added variety and challenge

## User Stories:
- As a user, I want to be able to control the snake's movement using arrow keys or swipe gestures on mobile devices.
- As a user, I want to see my score increase as the snake eats food and grows longer.
- As a user, I want to be able to restart the game if the snake collides with itself or the walls.
- As a user, I want to be able to select different mazes to play in for added variety.
- As a user, I want to be able to pause the game and resume playing later.

## Competitive Analysis:
- Python Snake Game: A simple snake game written in Python with basic functionality and a single maze.

## Competitive Quadrant Chart:
```mermaid
quadrantChart
    title Reach and engagement of snake games
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 Need to improve reach and engagement
    quadrant-2 Need to improve reach, high engagement
    quadrant-3 High reach, low engagement
    quadrant-4 High reach and engagement
    "Python Snake Game": [0.3, 0.4]
    "Our Target Product": [0.6, 0.7]
```
'''

SYSTEM_DESIGN = '''
## Implementation approach:
For the snake game implementation, we can use the Pygame library, which is a popular open-source library for game development in Python. Pygame provides a simple and efficient way to create games and handle user input, graphics, and sound.

To create multiple mazes for the game, we can define maze layouts as text files and load them dynamically during runtime. This approach allows for easy customization and expansion of maze options without modifying the code.

## Python package name:
```python
"snake_game"
```

## File list:
```python
[
    "main.py",
    "game.py",
    "snake.py",
    "food.py",
    "maze.py",
    "assets/",
    "mazes/"
]
```

## Data structures and interface definitions:
```mermaid
classDiagram
    class Game {
        -int score
        -Snake snake
        -Food food
        -Maze maze
        +start_game() : None
        +update() : None
        +handle_input(key: int) : None
        +check_collision() : None
        +draw() : None
        +game_over() : None
    }
    class Snake {
        -List[Tuple[int, int]] body
        -Tuple[int, int] direction
        +move() : None
        +grow() : None
        +change_direction(new_direction: Tuple[int, int]) : None
        +check_collision() : bool
        +draw() : None
    }
    class Food {
        -Tuple[int, int] position
        +generate() : None
        +draw() : None
    }
    class Maze {
        -List[List[int]] layout
        +load_maze(file_path: str) : None
        +draw() : None
    }
```

## Program call flow:
```mermaid
sequenceDiagram
    participant M as Main
    participant G as Game
    participant S as Snake
    participant F as Food
    participant Z as Maze

    M->>G: start_game()
    G->>S: move()
    G->>F: generate()
    G->>Z: load_maze(file_path)
    G->>G: update()
    G->>G: handle_input(key)
    G->>G: check_collision()
    G->>G: draw()
    G->>G: game_over()
```
'''


TASKS = '''
## Logic Analysis:
```python
[
    ("main.py", "Contains the main entry point of the game"),
    ("game.py", "Contains the Game class, responsible for managing the game state and logic"),
    ("snake.py", "Contains the Snake class, responsible for controlling the snake's movement"),
    ("food.py", "Contains the Food class, responsible for generating and drawing the food"),
    ("maze.py", "Contains the Maze class, responsible for loading and drawing the maze layout"),
]
```

## Task list:
```python
[
    "main.py",
    "game.py",
    "snake.py",
    "food.py",
    "maze.py"
]
```

## Shared Knowledge:
```python
"""
The 'game.py' file contains the main logic for the snake game, including the Game class which manages the game state and logic.

The 'snake.py' file contains the Snake class which controls the movement of the snake.

The 'food.py' file contains the Food class which generates and draws the food for the snake.

The 'maze.py' file contains the Maze class which loads and draws the maze layout for the game.
"""
'''


class MockMessages:
    req = Message(role="Boss", content=BOSS_REQUIREMENT,
                  cause_by=BossRequirement)
    prd = Message(role="Product Manager", content=PRD, cause_by=WritePRD)
    system_design = Message(
        role="Architect", content=SYSTEM_DESIGN, cause_by=WriteDesign)
    tasks = Message(role="Project Manager", content=TASKS, cause_by=WriteTasks)
