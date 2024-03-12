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
from metagpt.logs import logger
from metagpt.schema import CodeSummarizeContext
from tests.mock.mock_llm import MockLLM

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

mock_rsp = """
```mermaid
classDiagram
    class Game{
        +int score
        +int level
        +Snake snake
        +Food food
        +start_game() void
        +initialize_game() void
        +game_loop() void
        +update() void
        +draw() void
        +handle_events() void
        +check_collision() void
        +increase_score() void
        +increase_level() void
        +game_over() void
        Game()
    }
    class Snake{
        +list body
        +tuple direction
        +move() void
        +change_direction(direction: str) void
        +grow() void
        +get_head() tuple
        +get_body() list
        Snake()
    }
    class Food{
        +tuple position
        +generate() void
        +get_position() tuple
        Food()
    }
    Game "1" -- "1" Snake: has
    Game "1" -- "1" Food: has
```

```sequenceDiagram
participant M as Main
participant G as Game
participant S as Snake
participant F as Food
M->>G: start_game()
G->>G: initialize_game()
G->>G: game_loop()
G->>S: move()
G->>S: change_direction()
G->>S: grow()
G->>F: generate()
S->>S: move()
S->>S: change_direction()
S->>S: grow()
F->>F: generate()
```

## Summary
The code consists of the main game logic, including the Game, Snake, and Food classes. The game loop is responsible for updating and drawing the game elements, handling events, checking collisions, and managing the game state. The Snake class handles the movement, growth, and direction changes of the snake, while the Food class is responsible for generating and tracking the position of food items.

## TODOs
- Modify 'game.py' to add the implementation of obstacle handling and interaction with the game loop.
- Implement 'obstacle.py' to include the methods for spawning, moving, and disappearing of obstacles, as well as collision detection with the snake.
- Update 'main.py' to initialize the obstacle and incorporate it into the game loop.
- Update the mermaid call flow diagram to include the interaction with the obstacle.

```python
{
  "files_to_modify": {
    "game.py": "Add obstacle handling and interaction with the game loop",
    "obstacle.py": "Implement obstacle class with necessary methods",
    "main.py": "Initialize the obstacle and incorporate it into the game loop"
  }
}
```
"""


@pytest.mark.asyncio
async def test_summarize_code(context, mocker):
    context.src_workspace = context.git_repo.workdir / "src"
    await context.repo.docs.system_design.save(filename="1.json", content=DESIGN_CONTENT)
    await context.repo.docs.task.save(filename="1.json", content=TASK_CONTENT)
    await context.repo.with_src_path(context.src_workspace).srcs.save(filename="food.py", content=FOOD_PY)
    assert context.repo.srcs.workdir == context.src_workspace
    await context.repo.srcs.save(filename="game.py", content=GAME_PY)
    await context.repo.srcs.save(filename="main.py", content=MAIN_PY)
    await context.repo.srcs.save(filename="snake.py", content=SNAKE_PY)
    mocker.patch.object(MockLLM, "_mock_rsp", return_value=mock_rsp)

    all_files = context.repo.srcs.all_files
    summarization_context = CodeSummarizeContext(
        design_filename="1.json", task_filename="1.json", codes_filenames=all_files
    )
    action = SummarizeCode(context=context, i_context=summarization_context)
    rsp = await action.run()
    assert rsp
    logger.info(rsp)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
