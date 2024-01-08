#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_project_management_an.py
"""
import pytest

from metagpt.actions.project_management_an import REFINED_PM_NODES
from metagpt.llm import LLM

CONTEXT = """
### Legacy Content
{
  "Required Python packages": [
    "pygame==2.0.1"
  ],
  "Required Other language third-party packages": [
    "No third-party dependencies required"
  ],
  "Logic Analysis": [
    [
      "constants.py",
      "Contains all the constants like GRID_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT, BACKGROUND_COLOR, TILE_COLORS"
    ],
    [
      "game.py",
      "Contains Game class with methods for game logic such as move, undo, check_game_over, and reset_game"
    ],
    [
      "ui.py",
      "Contains UI class responsible for drawing the grid, displaying scores, showing game over, and undo button"
    ],
    [
      "main.py",
      "Contains Main class which initializes the game loop and orchestrates the interactions between Game and UI classes"
    ]
  ],
  "Task list": [
    "constants.py",
    "game.py",
    "ui.py",
    "main.py"
  ],
  "Full API spec": "",
  "Shared Knowledge": "`constants.py` contains constants shared across `game.py` and `ui.py`. The Main class in `main.py` acts as the controller orchestrating the game flow and UI updates.",
  "Anything UNCLEAR": "The specifics of the scoring system and how the high score is stored and retrieved need to be clarified. Additionally, the exact graphical assets and animations for the game are not specified."
}

### New Requirements
{
    "Refined Implementation Approach": "We will refine our implementation approach to accommodate the new 8x8 grid and the increased winning score target of 4096. This will involve optimizing the game's core logic to handle the larger grid size efficiently and updating the scoring system. We will also enhance the UI to ensure it remains user-friendly and visually appealing with the new grid. The undo feature will be adapted to work seamlessly with the increased complexity of the game.",
    "File list": [
        "main.py",
        "game.py",
        "ui.py",
        "constants.py"
    ],
    "Refined Data Structures and Interfaces": "classDiagram
    class Main {
        +pygame: PygameInstance
        +game: Game
        +ui: UI
        +run() void
    }
    class Game {
        -grid: list
        -current_score: int
        -high_score: int
        -last_move: list
        -target_score: int
        +__init__(grid_size: int, target_score: int)
        +move(direction: str) bool
        +undo() bool
        +check_game_over() bool
        +reset_game() void
        +update_score(value: int) void
    }
    class UI {
        -screen: PygameSurface
        -font: PygameFont
        +__init__(screen_size: tuple, grid_size: int)
        +draw_grid(grid: list) void
        +display_score(current_score: int, high_score: int) void
        +show_game_over() void
        +show_undo_button() void
        +update_ui_for_larger_grid() void
    }
    class Constants {
        +GRID_SIZE: int = 8
        +TARGET_SCORE: int = 4096
        +WINDOW_WIDTH: int
        +WINDOW_HEIGHT: int
        +BACKGROUND_COLOR: tuple
        +TILE_COLORS: dict
    }
    Main --> Game
    Main --> UI
    Game --> Constants
    UI --> Constants",
    "Refined Program call flow": "sequenceDiagram
    participant M as Main
    participant G as Game
    participant U as UI
    M->>G: create instance(grid_size: Constants.GRID_SIZE, target_score: Constants.TARGET_SCORE)
    M->>U: create instance(screen_size: (Constants.WINDOW_WIDTH, Constants.WINDOW_HEIGHT), grid_size: Constants.GRID_SIZE)
    loop game loop
        M->>U: draw_grid(G.grid)
        M->>U: display_score(G.current_score, G.high_score)
        M->>U: show_undo_button()
        M->>G: move(direction)
        alt if move is valid
            G-->>M: return true
            M->>G: update_score(value)
        else if move is invalid
            G-->>M: return false
        end
        alt if undo is triggered
            M->>G: undo()
            G-->>M: return true
        else no undo
            G-->>M: return false
        end
        alt if game over
            M->>U: show_game_over()
            M->>G: reset_game()
        end
    end",
    "Anything UNCLEAR": "It remains unclear if the undo feature should have limitations on its use, such as a maximum number of undos per game or if it should be available without restriction. Further clarification on this aspect would be beneficial."
}
"""


@pytest.fixture()
def llm():
    return LLM()


@pytest.mark.asyncio
async def test_project_management_an(llm):
    node = await REFINED_PM_NODES.fill(CONTEXT, llm)
    assert node.instruct_content
    assert "Refined Logic Analysis" in node.instruct_content.model_dump_json()
