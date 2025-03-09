import asyncio
import os

from metagpt.roles.architect import Architect
from metagpt.schema import Message

DESIGN_DOC_SNAKE = """
{
    "Implementation approach": "We will use the Pygame library to create the CLI-based snake game. Pygame is a set of Python modules designed for writing video games, which will help us handle graphics, sound, and input. The game will be structured into different modules to handle the main game loop, snake movement, food generation, collision detection, and user interface. We will ensure the game is engaging and responsive by optimizing the game loop and input handling. The score display and different speed levels will be implemented to enhance the user experience.",
    "File list": [
        "main.py",
        "game.py",
        "snake.py",
        "food.py",
        "ui.py"
    ],
    "Data structures and interfaces": "\nclassDiagram\n    class Main {\n        +main() void\n    }\n    class Game {\n        -Snake snake\n        -Food food\n        -int score\n        -int speed\n        +__init__(speed: int)\n        +run() void\n        +restart() void\n        +update_score() void\n    }\n    class Snake {\n        -list body\n        -str direction\n        +__init__()\n        +move() void\n        +change_direction(new_direction: str) void\n        +check_collision() bool\n        +grow() void\n    }\n    class Food {\n        -tuple position\n        +__init__()\n        +generate_new_position() void\n    }\n    class UI {\n        +display_score(score: int) void\n        +display_game_over() void\n        +display_game(snake: Snake, food: Food) void\n    }\n    Main --> Game\n    Game --> Snake\n    Game --> Food\n    Game --> UI\n",
    "Program call flow": "\nsequenceDiagram\n    participant M as Main\n    participant G as Game\n    participant S as Snake\n    participant F as Food\n    participant U as UI\n    M->>G: __init__(speed)\n    M->>G: run()\n    G->>S: __init__()\n    G->>F: __init__()\n    loop Game Loop\n        G->>S: move()\n        G->>S: check_collision()\n        alt Collision Detected\n            G->>G: restart()\n            G->>U: display_game_over()\n        else No Collision\n            G->>F: generate_new_position()\n            G->>S: grow()\n            G->>G: update_score()\n            G->>U: display_score(score)\n        end\n        G->>U: display_game(snake, food)\n    end\n",
    "Anything UNCLEAR": "Currently, all aspects of the project are clear."
}
"""

WRITE_SNAKE = """Write a system design for a cli snake game with pygame"""

REWRITE_SNAKE = """Rewrite the system design at temp_design.json, add a web UI"""

CASUAL_CHAT = """What's your name?"""


async def main(requirement):
    with open("temp_design.json", "w") as f:
        f.write(DESIGN_DOC_SNAKE)
    architect = Architect()
    await architect.run(Message(content=requirement, send_to="Bob"))
    os.remove("temp_design.json")


if __name__ == "__main__":
    asyncio.run(main(REWRITE_SNAKE))
