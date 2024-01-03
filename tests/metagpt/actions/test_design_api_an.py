#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_design_api_an.py.py
"""
import pytest

from metagpt.actions.design_api_an import REFINED_DESIGN_NODES
from metagpt.provider import OpenAIGPTAPI

CONTEXT = """
### Legacy Content
{
  "Implementation approach": "We will use Python with the Pygame library to develop the core mechanics of the 2048 game. The game will feature a simple and intuitive user interface, score tracking with high score memory, and an undo move feature. We'll ensure the game has visually appealing graphics and animations while maintaining a minimalist design. The undo feature will allow a single move to be undone without affecting the score, to keep the implementation straightforward.",
  "File list": [
    "main.py",
    "game.py",
    "ui.py",
    "constants.py"
  ],
  "Data structures and interfaces": "classDiagram\n    class Main {\n        +pygame: PygameInstance\n        +game: Game\n        +run() void\n    }\n    class Game {\n        -grid: list\n        -current_score: int\n        -high_score: int\n        -last_move: list\n        +move(direction: str) bool\n        +undo() bool\n        +check_game_over() bool\n        +reset_game() void\n    }\n    class UI {\n        -screen: PygameSurface\n        -font: PygameFont\n        +draw_grid(grid: list) void\n        +display_score(current_score: int, high_score: int) void\n        +show_game_over() void\n        +show_undo_button() void\n    }\n    class Constants {\n        +GRID_SIZE: int\n        +WINDOW_WIDTH: int\n        +WINDOW_HEIGHT: int\n        +BACKGROUND_COLOR: tuple\n        +TILE_COLORS: dict\n    }\n    Main --> Game\n    Main --> UI\n    Game --> Constants\n    UI --> Constants",
  "Program call flow": "sequenceDiagram\n    participant M as Main\n    participant G as Game\n    participant U as UI\n    M->>G: create instance\n    M->>U: create instance\n    loop game loop\n        M->>U: draw_grid(G.grid)\n        M->>U: display_score(G.current_score, G.high_score)\n        M->>U: show_undo_button()\n        M->>G: move(direction)\n        alt if move is valid\n            G-->>M: return true\n        else if move is invalid\n            G-->>M: return false\n        end\n        alt if undo is triggered\n            M->>G: undo()\n            G-->>M: return true\n        else no undo\n            G-->>M: return false\n        end\n        alt if game over\n            M->>U: show_game_over()\n            M->>G: reset_game()\n        end\n    end",
  "Anything UNCLEAR": "The specifics of the scoring system and how the high score is stored and retrieved need to be clarified. Additionally, the exact graphical assets and animations for the game are not specified."
}

### New Requirements
{
    "Language": "en_us",
    "Programming Language": "Python",
    "Refined Requirements": "Update the py2048_game to have a larger 8x8 grid and a new winning score target of 4096, while maintaining the core mechanics and user-friendly interface of the original 2048 game.",
    "Project Name": "py2048_game",
    "Refined Product Goals": [
        "Develop an enhanced version of the 2048 game with a larger grid and higher score target to provide a new challenge to players",
        "Ensure the game remains visually appealing and maintains a consistent theme with the added complexity",
        "Implement smooth and responsive game controls suitable for an 8x8 grid interface"
    ],
    "Refined User Stories": [
        "As a player, I want to experience a clear and simple interface on an 8x8 grid so that I can focus on the gameplay",
        "As a player, I want to aim for a higher score target of 4096 to challenge my skills further",
        "As a player, I want to see my current and high scores to track my progress on the new larger grid",
        "As a player, I want the option to undo my last move to improve my strategy on the 8x8 grid",
        "As a player, I want the game to perform smoothly despite the increased complexity of the larger grid"
    ],
    "Competitive Analysis": [
        "2048 Original: Classic gameplay with minimalistic design, but lacks modern features",
        "2048 by Gabriele Cirulli: Open-source version with clean UI, but no additional features",
        "2048 Hex: Unique hexagon board, providing a different challenge",
        "2048 Multiplayer: Allows playing against others, but the interface is cluttered",
        "2048 with AI: Includes AI challenge mode, but the AI is often too difficult for casual players",
        "2048.io: Combines 2048 gameplay with .io style, though it can be overwhelming for new players",
        "2048 Animated: Features animations, but has performance issues on some devices"
    ],
    "Competitive Quadrant Chart": "quadrantChart\n    title \"2048 Game Market Positioning\"\n    x-axis \"Basic Features\" --> \"Advanced Features\"\n    y-axis \"Low User Engagement\" --> \"High User Engagement\"\n    quadrant-1 \"Niche Innovators\"\n    quadrant-2 \"Market Leaders\"\n    quadrant-3 \"Emerging Contenders\"\n    quadrant-4 \"Falling Behind\"\n    \"2048 Original\": [0.2, 0.7]\n    \"2048 by Gabriele Cirulli\": [0.3, 0.8]\n    \"2048 Hex\": [0.5, 0.4]\n    \"2048 Multiplayer\": [0.6, 0.6]\n    \"2048 with AI\": [0.7, 0.5]\n    \"2048.io\": [0.4, 0.3]\n    \"2048 Animated\": [0.3, 0.2]\n    \"Our Target Product\": [0.9, 0.9]",
    "Incremental Requirement Analysis": [
        "Adjust the game logic to accommodate an 8x8 grid while ensuring performance remains optimal",
        "Update the UI to fit the larger grid and include visual cues for the new score target",
        "Enhance the scoring system to support the new target of 4096",
        "Ensure the undo feature is adapted to work with the larger grid and increased game complexity",
        "Test the game thoroughly to maintain a smooth and responsive experience on the new 8x8 grid"
    ],
    "Refined Requirement Pool": [
        [
            "P0",
            "Expand the game grid to 8x8 and adjust the core mechanics accordingly"
        ],
        [
            "P0",
            "Increase the score target to 4096 and update the scoring system"
        ],
        [
            "P1",
            "Redesign the user interface to accommodate the larger grid size"
        ],
        [
            "P1",
            "Ensure the undo move feature is compatible with the new grid and score target"
        ],
        [
            "P2",
            "Optimize game performance for the increased complexity of an 8x8 grid"
        ],
        [
            "P2",
            "Maintain a visually appealing and consistent theme with the updated game features"
        ]
    ],
    "UI Design draft": "The UI will be updated to feature an 8x8 grid while maintaining a minimalist design. The main game screen will display the larger game grid, current score, high score, and an undo button. The color scheme and transitions will be adapted to ensure clarity and pleasant aesthetics despite the increased grid size.",
    "Anything UNCLEAR": "The specifics of how the undo feature should work with the larger grid size and whether there should be any limitations on its use need to be clarified."
}
"""


@pytest.fixture()
def llm():
    return OpenAIGPTAPI()


@pytest.mark.asyncio
async def test_write_design_an():
    node = await REFINED_DESIGN_NODES.fill(CONTEXT, llm)
    assert node.instruct_content
    assert "Refined Data Structures and Interfaces" in node.instruct_content.json(ensure_ascii=False)
