#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/24 20:32
@Author  : alexanderwu
@File    : mock_json.py
"""

PRD = {
    "Language": "zh_cn",
    "Programming Language": "Python",
    "Original Requirements": "写一个简单的cli贪吃蛇",
    "Project Name": "cli_snake",
    "Product Goals": ["创建一个简单易用的贪吃蛇游戏", "提供良好的用户体验", "支持不同难度级别"],
    "User Stories": [
        "作为玩家，我希望能够选择不同的难度级别",
        "作为玩家，我希望在每局游戏结束后能够看到我的得分",
        "作为玩家，我希望在输掉游戏后能够重新开始",
        "作为玩家，我希望看到简洁美观的界面",
        "作为玩家，我希望能够在手机上玩游戏",
    ],
    "Competitive Analysis": ["贪吃蛇游戏A：界面简单，缺乏响应式特性", "贪吃蛇游戏B：美观且响应式的界面，显示最高得分", "贪吃蛇游戏C：响应式界面，显示最高得分，但有很多广告"],
    "Competitive Quadrant Chart": 'quadrantChart\n    title "Reach and engagement of campaigns"\n    x-axis "Low Reach" --> "High Reach"\n    y-axis "Low Engagement" --> "High Engagement"\n    quadrant-1 "We should expand"\n    quadrant-2 "Need to promote"\n    quadrant-3 "Re-evaluate"\n    quadrant-4 "May be improved"\n    "Game A": [0.3, 0.6]\n    "Game B": [0.45, 0.23]\n    "Game C": [0.57, 0.69]\n    "Game D": [0.78, 0.34]\n    "Game E": [0.40, 0.34]\n    "Game F": [0.35, 0.78]\n    "Our Target Product": [0.5, 0.6]',
    "Requirement Analysis": "",
    "Requirement Pool": [["P0", "主要代码..."], ["P0", "游戏算法..."]],
    "UI Design draft": "基本功能描述，简单的风格和布局。",
    "Anything UNCLEAR": "",
}


DESIGN = {
    "Implementation approach": "我们将使用Python编程语言，并选择合适的开源框架来实现贪吃蛇游戏。我们将分析需求中的难点，并选择合适的开源框架来简化开发流程。",
    "File list": ["main.py", "game.py"],
    "Data structures and interfaces": "\nclassDiagram\n    class Game {\n        -int width\n        -int height\n        -int score\n        -int speed\n        -List<Point> snake\n        -Point food\n        +__init__(width: int, height: int, speed: int)\n        +start_game()\n        +change_direction(direction: str)\n        +game_over()\n        +update_snake()\n        +update_food()\n        +check_collision()\n    }\n    class Point {\n        -int x\n        -int y\n        +__init__(x: int, y: int)\n    }\n    Game --> Point\n",
    "Program call flow": "\nsequenceDiagram\n    participant M as Main\n    participant G as Game\n    M->>G: start_game()\n    M->>G: change_direction(direction)\n    G->>G: update_snake()\n    G->>G: update_food()\n    G->>G: check_collision()\n    G-->>G: game_over()\n",
    "Anything UNCLEAR": "",
}


TASK = {
    "Required Python packages": ["pygame==2.0.1"],
    "Required Other language third-party packages": ["No third-party dependencies required"],
    "Logic Analysis": [
        ["game.py", "Contains Game class and related functions for game logic"],
        ["main.py", "Contains the main function, imports Game class from game.py"],
    ],
    "Task list": ["game.py", "main.py"],
    "Full API spec": "",
    "Shared Knowledge": "'game.py' contains functions shared across the project.",
    "Anything UNCLEAR": "",
}


FILE_GAME = """## game.py

import pygame
import random

class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

class Game:
    def __init__(self, width: int, height: int, speed: int):
        self.width = width
        self.height = height
        self.score = 0
        self.speed = speed
        self.snake = [Point(width // 2, height // 2)]
        self.food = self._create_food()

    def start_game(self):
        pygame.init()
        self._display = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake Game')
        self._clock = pygame.time.Clock()
        self._running = True

        while self._running:
            self._handle_events()
            self._update_snake()
            self._update_food()
            self._check_collision()
            self._draw_screen()
            self._clock.tick(self.speed)

    def change_direction(self, direction: str):
        # Update the direction of the snake based on user input
        pass

    def game_over(self):
        # Display game over message and handle game over logic
        pass

    def _create_food(self) -> Point:
        # Create and return a new food Point
        return Point(random.randint(0, self.width - 1), random.randint(0, self.height - 1))

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

    def _update_snake(self):
        # Update the position of the snake based on its direction
        pass

    def _update_food(self):
        # Update the position of the food if the snake eats it
        pass

    def _check_collision(self):
        # Check for collision between the snake and the walls or itself
        pass

    def _draw_screen(self):
        self._display.fill((0, 0, 0))  # Clear the screen
        # Draw the snake and food on the screen
        pygame.display.update()

if __name__ == "__main__":
    game = Game(800, 600, 15)
    game.start_game()
"""

FILE_GAME_CR_1 = """## Code Review: game.py
1. Yes, the code is implemented as per the requirements. It initializes the game with the specified width, height, and speed, and starts the game loop.
2. No, the logic for handling events and updating the snake, food, and collision is not implemented. To correct this, we need to implement the logic for handling events, updating the snake and food positions, and checking for collisions.
3. Yes, the existing code follows the "Data structures and interfaces" by defining the Game and Point classes with the specified attributes and methods.
4. No, several functions such as change_direction, game_over, _update_snake, _update_food, and _check_collision are not implemented. These functions need to be implemented to complete the game logic.
5. Yes, all necessary pre-dependencies have been imported. The required pygame package is imported at the beginning of the file.
6. No, methods from other files are not being reused as there are no other files being imported or referenced in the current code.

## Actions
1. Implement the logic for handling events, updating the snake and food positions, and checking for collisions within the Game class.
2. Implement the change_direction and game_over methods to handle user input and game over logic.
3. Implement the _update_snake method to update the position of the snake based on its direction.
4. Implement the _update_food method to update the position of the food if the snake eats it.
5. Implement the _check_collision method to check for collision between the snake and the walls or itself.

## Code Review Result
LBTM"""
