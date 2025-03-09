import asyncio
import sys
import uuid
from pathlib import Path

from metagpt.logs import logger
from metagpt.roles.di.engineer2 import Engineer2

DESIGN_DOC_2048 = '{"Implementation approach":"We will use the Pygame library to implement the 2048 game logic and user interface. Pygame is a set of Python modules designed for writing video games, which will help us create a responsive and visually appealing UI. For the mobile responsiveness, we will ensure that the game scales appropriately on different screen sizes. We will also use the Pygame GUI library to create buttons for restarting the game and choosing difficulty levels.","File list":["main.py","game.py","ui.py"],"Data structures and interfaces":"\\nclassDiagram\\n    class Game {\\n        -grid: list[list[int]]\\n        -score: int\\n        +__init__()\\n        +move(direction: str) bool\\n        +merge() bool\\n        +spawn_tile() None\\n        +is_game_over() bool\\n        +reset() None\\n    }\\n    class UI {\\n        -game: Game\\n        +__init__(game: Game)\\n        +draw_grid() None\\n        +draw_score() None\\n        +draw_buttons() None\\n        +handle_input() None\\n    }\\n    class Main {\\n        -ui: UI\\n        +main() None\\n    }\\n    Main --> UI\\n    UI --> Game\\n","Program call flow":"\\nsequenceDiagram\\n    participant M as Main\\n    participant U as UI\\n    participant G as Game\\n    M->>U: __init__(game)\\n    U->>G: __init__()\\n    M->>U: draw_grid()\\n    U->>G: move(direction)\\n    G-->>U: return bool\\n    U->>G: merge()\\n    G-->>U: return bool\\n    U->>G: spawn_tile()\\n    G-->>U: return None\\n    U->>G: is_game_over()\\n    G-->>U: return bool\\n    U->>G: reset()\\n    G-->>U: return None\\n    M->>U: draw_score()\\n    M->>U: draw_buttons()\\n    M->>U: handle_input()\\n","Anything UNCLEAR":"Clarification needed on the specific design elements for the UI to ensure it meets the \'beautiful\' requirement. Additionally, we need to confirm the exact difficulty levels and how they should affect the game mechanics."}'
TASK_DOC_2048 = '{"Required Python packages":["pygame==2.0.1","pygame_gui==0.5.7"],"Required Other language third-party packages":["No third-party dependencies required"],"Logic Analysis":[["game.py","Contains Game class with methods: __init__, move, merge, spawn_tile, is_game_over, reset"],["ui.py","Contains UI class with methods: __init__, draw_grid, draw_score, draw_buttons, handle_input"],["main.py","Contains Main class with method: main, initializes UI and Game"]],"Task list":["game.py","ui.py","main.py"],"Full API spec":"","Shared Knowledge":"`game.py` contains core game logic and state management. `ui.py` handles all user interface elements and interactions. `main.py` serves as the entry point to initialize and run the game.","Anything UNCLEAR":"Clarification needed on the specific design elements for the UI to ensure it meets the \'beautiful\' requirement. Additionally, we need to confirm the exact difficulty levels and how they should affect the game mechanics."}'
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
TASK_DOC_SNAKE = """
{
    "Required Python packages": [
        "pygame==2.0.1"
    ],
    "Required Other language third-party packages": [
        "No third-party dependencies required"
    ],
    "Logic Analysis": [
        [
            "main.py",
            "Contains the main function to initialize and start the game. Imports Game from game.py."
        ],
        [
            "game.py",
            "Contains the Game class which manages the game loop, score, and speed. Imports Snake from snake.py, Food from food.py, and UI from ui.py."
        ],
        [
            "snake.py",
            "Contains the Snake class which handles snake movement, direction changes, collision detection, and growth."
        ],
        [
            "food.py",
            "Contains the Food class which handles food position generation."
        ],
        [
            "ui.py",
            "Contains the UI class which handles displaying the score, game over screen, and the game state."
        ]
    ],
    "Task list": [
        "snake.py",
        "food.py",
        "ui.py",
        "game.py",
        "main.py"
    ],
    "Full API spec": "",
    "Shared Knowledge": "`game.py` contains the main game loop and integrates all other modules (snake, food, UI).",
    "Anything UNCLEAR": "Currently, all aspects of the project are clear."
}
"""

GAME_REQ_2048 = f"""
Create a 2048 game, follow the design doc and task doc. Write your code under /Users/gary/Files/temp/workspace/2048_game/src.
After writing all codes, write a code review for the codes, make improvement or adjustment based on the review.
Notice: You MUST implement the full code, don't leave comment without implementation!
Design doc:
{DESIGN_DOC_2048}
Task doc:
{TASK_DOC_2048}
"""
GAME_REQ_SNAKE = f"""
Create a snake game, follow the design doc and task doc. Write your code under /Users/gary/Files/temp/workspace/snake_game/src.
After writing all codes, write a code review for the codes, make improvement or adjustment based on the review.
Notice: You MUST implement the full code, don't leave comment without implementation!
Design doc:
{DESIGN_DOC_SNAKE}
Task doc:
{TASK_DOC_SNAKE}
"""
GAME_REQ_2048_NO_DOC = """
Create a 2048 game with pygame. Write your code under /Users/gary/Files/temp/workspace/2048_game/src.
Consider what files you will write, break down the requests to multiple tasks and write one file in each task.
After writing all codes, write a code review for the codes, make improvement or adjustment based on the review.
Notice: You MUST implement the full code, don't leave comment without implementation!
"""
GAME_INC_REQ_2048 = """
I found an issue with the 2048 code: when tiles are merged, no new tiles pop up.
Write code review for the codes (game.py, main.py, ui.py) under under /Users/gary/Files/temp/workspace/2048_game_bugs/src.
Then correct any issues you find. You can review all code in one time, and solve issues in one time.
"""
GAME_INC_REQ_SNAKE = """
Found this issue, TypeError: generate_new_position() missing 1 required positional argument: 'snake_body'
Write code review for the codes (food.py, game.py, main.py, snake.py, ui.py) under under /Users/gary/Files/temp/workspace/snake_game_bugs/src.
Then correct any issues you find. You can review all code in one time, and solve issues in one time.
"""
CASUAL_CHAT = """what's your name?"""


# increment development
INC_DEVELOPMENT_CASE1 = [
    "Complete the Snake game with the root directory at '/home/mgx/mgx/MetaGPT/workspace/snake_game'",
    "Use the up button to control the snake to move down, the left button to move right, and so on",
    "Place the restart/start button at the top",
    "Add a pause button",
    "Display the score and leaderboard in real-time on the page",
]

INC_DEVELOPMENT_CASE2 = [
    "Develop a Snake game using Python in the '/home/mgx/mgx/MetaGPT/workspace/snake_game_py' folder",
    "Change the title to 'Special Snake'",
    "Use the up button to control the snake to move down, the left button to move right, and so on",
    "Add a pause button",
    "Display the score and leaderboard in real-time on the page",
    "Design a more attractive style for the leaderboard",
]

INC_DEVELOPMENT_CASE3 = [
    "Complete the 2048 game with the root directory at '/home/mgx/mgx/MetaGPT/workspace/2048_game'",
    "Place the start button at the top",
    "Display the score and leaderboard in real-time on the page",
    "Design a more attractive style for the leaderboard",
    "Add a restart button",
]

INC_DEVELOPMENT_CASE4 = [
    "Develop a 2048 game using Python in the '/home/mgx/mgx/MetaGPT/workspace/2048_game_py' folder",
    "Display the score and leaderboard in real-time on the page",
    "Add a restart button",
]
INC_DEVELOPMENT_CASE5 = [
    "Root path is '/home/mgx/mgx/MetaGPT/workspace/to_list' Create a website widget for TODO list management. Users should be able to add, mark as complete, and delete tasks. Include features like prioritization, due dates, and categories. Make it visually appealing, responsive, and user-friendly. Use HTML, CSS, and JavaScript. Consider additional features like notifications or task export. Keep it simple and enjoyable for users.dont use vue or react.dont use third party library, use localstorage to save data.",
    "Add a `clean all` buttonn",
]
INC_DEVELOPMENT_CASE6 = [
    '使用原生HTML开发一个塔罗牌角色介绍网站\n1. 主题是塔罗牌占卜的网站\n2. 超前的网页布局\n3. 页面需要时响应式的\n4. 页面需要美观大气 root path "”/home/mgx/mgx/MetaGPT/workspace/taro"',
    "扩充更多的角色，添加3个自己想出来的角色",
    "让每一个角色的描述更加清楚",
    "将中文内容全部替换为英文包括js里面的内容",
]


async def increment_development():
    engineer2 = Engineer2(run_eval=True)
    example = INC_DEVELOPMENT_CASE6
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(Path("logs") / f"{str(uuid.uuid4())[-12:]}.log", level="DEBUG")
    logger.info("user requirement:\n" + "\n".join(example))
    try:
        for user_requirement in example:
            logger.info(f"input:{user_requirement}")
            await engineer2.run(user_requirement)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(increment_development())
    # engineer2 = Engineer2()
    # asyncio.run(engineer2.run(GAME_REQ_2048_NO_DOC))
