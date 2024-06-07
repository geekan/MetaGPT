import asyncio
import os

from metagpt.roles.project_manager import ProjectManager
from metagpt.schema import Message

DESIGN_DOC_2048 = '{"Implementation approach":"We will use the Pygame library to implement the 2048 game logic and user interface. Pygame is a set of Python modules designed for writing video games, which will help us create a responsive and visually appealing UI. For the mobile responsiveness, we will ensure that the game scales appropriately on different screen sizes. We will also use the Pygame GUI library to create buttons for restarting the game and choosing difficulty levels.","File list":["main.py","game.py","ui.py"],"Data structures and interfaces":"\\nclassDiagram\\n    class Game {\\n        -grid: list[list[int]]\\n        -score: int\\n        +__init__()\\n        +move(direction: str) bool\\n        +merge() bool\\n        +spawn_tile() None\\n        +is_game_over() bool\\n        +reset() None\\n    }\\n    class UI {\\n        -game: Game\\n        +__init__(game: Game)\\n        +draw_grid() None\\n        +draw_score() None\\n        +draw_buttons() None\\n        +handle_input() None\\n    }\\n    class Main {\\n        -ui: UI\\n        +main() None\\n    }\\n    Main --> UI\\n    UI --> Game\\n","Program call flow":"\\nsequenceDiagram\\n    participant M as Main\\n    participant U as UI\\n    participant G as Game\\n    M->>U: __init__(game)\\n    U->>G: __init__()\\n    M->>U: draw_grid()\\n    U->>G: move(direction)\\n    G-->>U: return bool\\n    U->>G: merge()\\n    G-->>U: return bool\\n    U->>G: spawn_tile()\\n    G-->>U: return None\\n    U->>G: is_game_over()\\n    G-->>U: return bool\\n    U->>G: reset()\\n    G-->>U: return None\\n    M->>U: draw_score()\\n    M->>U: draw_buttons()\\n    M->>U: handle_input()\\n","Anything UNCLEAR":"Clarification needed on the specific design elements for the UI to ensure it meets the \'beautiful\' requirement. Additionally, we need to confirm the exact difficulty levels and how they should affect the game mechanics."}'
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
REQ = """Write a project schedule based on the design at temp_design.json"""
CASUAL_CHAT = """what's your name?"""


async def main(requirement):
    with open("temp_design.json", "w") as f:
        f.write(DESIGN_DOC_2048)
    project_manager = ProjectManager()
    await project_manager.run(Message(content=requirement, send_to="Eve"))
    os.remove("temp_design.json")


if __name__ == "__main__":
    asyncio.run(main(REQ))
