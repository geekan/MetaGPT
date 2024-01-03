#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : mashenquan
@File    : test_summarize_code.py
@Modifiled By: mashenquan, 2023-12-6. Unit test for summarize_code.py
"""
import pytest

from metagpt.actions.summarize_code import SummarizeCode
from metagpt.config import CONFIG
from metagpt.const import SYSTEM_DESIGN_FILE_REPO, TASK_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import CodeSummarizeContext
from metagpt.utils.file_repository import FileRepository

DESIGN_CONTENT = """
{"Implementation approach": "To develop this snake game, we will use the Python language and choose the Pygame library. Pygame is an open-source Python module collection specifically designed for writing video games. It provides functionalities such as displaying images and playing sounds, making it suitable for creating intuitive and responsive user interfaces. We will ensure efficient game logic to prevent any delays during gameplay. The scoring system will be simple, with the snake gaining points for each food it eats. We will use Pygame's event handling system to implement pause and resume functionality, as well as high-score tracking. The difficulty will increase by speeding up the snake's movement. In the initial version, we will focus on single-player mode and consider adding multiplayer mode and customizable skins in future updates. Based on the new requirement, we will also add a moving obstacle that appears randomly. If the snake eats this obstacle, the game will end. If the snake does not eat the obstacle, it will disappear after 5 seconds. For this, we need to add mechanisms for obstacle generation, movement, and disappearance in the game logic.", "Project_name": "snake_game", "File list": ["main.py", "game.py", "snake.py", "food.py", "obstacle.py", "scoreboard.py", "constants.py", "assets/styles.css", "assets/index.html"], "Data structures and interfaces": "```mermaid\n    classDiagram\n        class Game{\n            +int score\n            +int speed\n            +bool game_over\n            +bool paused\n            +Snake snake\n            +Food food\n            +Obstacle obstacle\n            +Scoreboard scoreboard\n            +start_game() void\n            +pause_game() void\n            +resume_game() void\n            +end_game() void\n            +increase_difficulty() void\n            +update() void\n            +render() void\n            Game()\n        }\n        class Snake{\n            +list body_parts\n            +str direction\n            +bool grow\n            +move() void\n            +grow() void\n            +check_collision() bool\n            Snake()\n        }\n        class Food{\n            +tuple position\n            +spawn() void\n            Food()\n        }\n        class Obstacle{\n            +tuple position\n            +int lifetime\n            +bool active\n            +spawn() void\n            +move() void\n            +check_collision() bool\n            +disappear() void\n            Obstacle()\n        }\n        class Scoreboard{\n            +int high_score\n            +update_score(int) void\n            +reset_score() void\n            +load_high_score() void\n            +save_high_score() void\n            Scoreboard()\n        }\n        class Constants{\n        }\n        Game \"1\" -- \"1\" Snake: has\n        Game \"1\" -- \"1\" Food: has\n        Game \"1\" -- \"1\" Obstacle: has\n        Game \"1\" -- \"1\" Scoreboard: has\n    ```", "Program call flow": "```sequenceDiagram\n    participant M as Main\n    participant G as Game\n    participant S as Snake\n    participant F as Food\n    participant O as Obstacle\n    participant SB as Scoreboard\n    M->>G: start_game()\n    loop game loop\n        G->>S: move()\n        G->>S: check_collision()\n        G->>F: spawn()\n        G->>O: spawn()\n        G->>O: move()\n        G->>O: check_collision()\n        G->>O: disappear()\n        G->>SB: update_score(score)\n        G->>G: update()\n        G->>G: render()\n        alt if paused\n            M->>G: pause_game()\n            M->>G: resume_game()\n        end\n        alt if game_over\n            G->>M: end_game()\n        end\n    end\n```", "Anything UNCLEAR": "There is no need for further clarification as the requirements are already clear."}
"""

TASK_CONTENT = """
{"Required Python third-party packages": ["pygame==2.0.1"], "Required Other language third-party packages": ["No third-party packages required for other languages."], "Full API spec": "\n        openapi: 3.0.0\n        info:\n          title: Snake Game API\n          version: \"1.0.0\"\n        paths:\n          /start:\n            get:\n              summary: Start the game\n              responses:\n                '200':\n                  description: Game started successfully\n          /pause:\n            get:\n              summary: Pause the game\n              responses:\n                '200':\n                  description: Game paused successfully\n          /resume:\n            get:\n              summary: Resume the game\n              responses:\n                '200':\n                  description: Game resumed successfully\n          /end:\n            get:\n              summary: End the game\n              responses:\n                '200':\n                  description: Game ended successfully\n          /score:\n            get:\n              summary: Get the current score\n              responses:\n                '200':\n                  description: Current score retrieved successfully\n          /highscore:\n            get:\n              summary: Get the high score\n              responses:\n                '200':\n                  description: High score retrieved successfully\n        components: {}\n    ", "Logic Analysis": [["constants.py", "Contains all the constant values like screen size, colors, game speeds, etc. This should be implemented first as it provides the base values for other components."], ["snake.py", "Contains the Snake class with methods for movement, growth, and collision detection. It is dependent on constants.py for configuration values."], ["food.py", "Contains the Food class responsible for spawning food items on the screen. It is dependent on constants.py for configuration values."], ["obstacle.py", "Contains the Obstacle class with methods for spawning, moving, and disappearing of obstacles, as well as collision detection with the snake. It is dependent on constants.py for configuration values."], ["scoreboard.py", "Contains the Scoreboard class for updating, resetting, loading, and saving high scores. It may use constants.py for configuration values and depends on the game's scoring logic."], ["game.py", "Contains the main Game class which includes the game loop and methods for starting, pausing, resuming, and ending the game. It is dependent on snake.py, food.py, obstacle.py, and scoreboard.py."], ["main.py", "The entry point of the game that initializes the game and starts the game loop. It is dependent on game.py."]], "Task list": ["constants.py", "snake.py", "food.py", "obstacle.py", "scoreboard.py", "game.py", "main.py"], "Shared Knowledge": "\n        'constants.py' should contain all the necessary configurations for the game, such as screen dimensions, color definitions, and speed settings. These constants will be used across multiple files, ensuring consistency and ease of updates. Ensure that the Pygame library is initialized correctly in 'main.py' before starting the game loop. Also, make sure that the game's state is managed properly when pausing and resuming the game.\n    ", "Anything UNCLEAR": "The interaction between the 'obstacle.py' and the game loop needs to be clearly defined to ensure obstacles appear and disappear correctly. The lifetime of the obstacle and its random movement should be implemented in a way that does not interfere with the game's performance."}
"""

FOOD_PY = """
## food.py
import random

class Food:
    def __init__(self):
        self.position = (0, 0)

    def generate(self):
        x = random.randint(0, 9)
        y = random.randint(0, 9)
        self.position = (x, y)

    def get_position(self):
        return self.position

"""

GAME_PY = """
## game.py
import pygame
from snake import Snake
from food import Food

class Game:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.snake = Snake()
        self.food = Food()

    def start_game(self):
        pygame.init()
        self.initialize_game()
        self.game_loop()

    def initialize_game(self):
        self.score = 0
        self.level = 1
        self.snake.reset()
        self.food.generate()

    def game_loop(self):
        game_over = False

        while not game_over:
            self.update()
            self.draw()
            self.handle_events()
            self.check_collision()
            self.increase_score()
            self.increase_level()

            if self.snake.is_collision():
                game_over = True
                self.game_over()

    def update(self):
        self.snake.move()

    def draw(self):
        self.snake.draw()
        self.food.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.snake.change_direction("UP")
                elif event.key == pygame.K_DOWN:
                    self.snake.change_direction("DOWN")
                elif event.key == pygame.K_LEFT:
                    self.snake.change_direction("LEFT")
                elif event.key == pygame.K_RIGHT:
                    self.snake.change_direction("RIGHT")

    def check_collision(self):
        if self.snake.get_head() == self.food.get_position():
            self.snake.grow()
            self.food.generate()

    def increase_score(self):
        self.score += 1

    def increase_level(self):
        if self.score % 10 == 0:
            self.level += 1

    def game_over(self):
        print("Game Over")
        self.initialize_game()

"""

MAIN_PY = """
## main.py
import pygame
from game import Game

def main():
    pygame.init()
    game = Game()
    game.start_game()

if __name__ == "__main__":
    main()

"""

SNAKE_PY = """
## snake.py
import pygame

class Snake:
    def __init__(self):
        self.body = [(0, 0)]
        self.direction = (1, 0)

    def move(self):
        head = self.body[0]
        dx, dy = self.direction
        new_head = (head[0] + dx, head[1] + dy)
        self.body.insert(0, new_head)
        self.body.pop()

    def change_direction(self, direction):
        if direction == "UP":
            self.direction = (0, -1)
        elif direction == "DOWN":
            self.direction = (0, 1)
        elif direction == "LEFT":
            self.direction = (-1, 0)
        elif direction == "RIGHT":
            self.direction = (1, 0)

    def grow(self):
        tail = self.body[-1]
        dx, dy = self.direction
        new_tail = (tail[0] - dx, tail[1] - dy)
        self.body.append(new_tail)

    def get_head(self):
        return self.body[0]

    def get_body(self):
        return self.body[1:]

"""


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_summarize_code():
    CONFIG.src_workspace = CONFIG.git_repo.workdir / "src"
    await FileRepository.save_file(filename="1.json", relative_path=SYSTEM_DESIGN_FILE_REPO, content=DESIGN_CONTENT)
    await FileRepository.save_file(filename="1.json", relative_path=TASK_FILE_REPO, content=TASK_CONTENT)
    await FileRepository.save_file(filename="food.py", relative_path=CONFIG.src_workspace, content=FOOD_PY)
    await FileRepository.save_file(filename="game.py", relative_path=CONFIG.src_workspace, content=GAME_PY)
    await FileRepository.save_file(filename="main.py", relative_path=CONFIG.src_workspace, content=MAIN_PY)
    await FileRepository.save_file(filename="snake.py", relative_path=CONFIG.src_workspace, content=SNAKE_PY)

    src_file_repo = CONFIG.git_repo.new_file_repository(relative_path=CONFIG.src_workspace)
    all_files = src_file_repo.all_files
    ctx = CodeSummarizeContext(design_filename="1.json", task_filename="1.json", codes_filenames=all_files)
    action = SummarizeCode(context=ctx)
    rsp = await action.run()
    assert rsp
    logger.info(rsp)
