#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_write_prd_an.py
"""
import pytest

from metagpt.actions.write_prd_an import REFINE_PRD_NODE
from metagpt.provider import OpenAIGPTAPI

CONTEXT = """
### New Project Name
py2048_game

### New Requirements
Changed score target for 2048 game from 2048 to 4096.
Please change the game's score target from 2048 to 4096, and change the interface size from 4*4 to 8*8.

### Legacy Content
{
  "Language": "en_us",
  "Programming Language": "Python",
  "Original Requirements": "make a simple 2048 game based on pygame",
  "Project Name": "pygame_2048",
  "Product Goals": [
    "Develop a user-friendly and intuitive 2048 game",
    "Ensure the game is visually appealing and maintains a consistent theme",
    "Implement smooth and responsive game controls"
  ],
  "User Stories": [
    "As a player, I want to experience a clear and simple interface so that I can focus on the gameplay",
    "As a player, I want to see my current and high scores to track my progress",
    "As a player, I want the option to undo my last move to improve my strategy"
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
  "Competitive Quadrant Chart": "quadrantChart\n    title \"2048 Game Market Positioning\"\n    x-axis \"Basic Features\" --> \"Advanced Features\"\n    y-axis \"Low User Engagement\" --> \"High User Engagement\"\n    quadrant-1 \"Niche Innovators\"\n    quadrant-2 \"Market Leaders\"\n    quadrant-3 \"Emerging Contenders\"\n    quadrant-4 \"Falling Behind\"\n    \"2048 Original\": [0.2, 0.7]\n    \"2048 by Gabriele Cirulli\": [0.3, 0.8]\n    \"2048 Hex\": [0.5, 0.4]\n    \"2048 Multiplayer\": [0.6, 0.6]\n    \"2048 with AI\": [0.7, 0.5]\n    \"2048.io\": [0.4, 0.3]\n    \"2048 Animated\": [0.3, 0.2]\n    \"Our Target Product\": [0.8, 0.9]",
  "Requirement Analysis": "The game should be simple yet engaging, with a focus on smooth performance and an intuitive user interface. High scores and undo functionality are important to users for a competitive and strategic gameplay experience. Aesthetic appeal and a consistent theme will also contribute to the game's success.",
  "Requirement Pool": [
    [
      "P0",
      "Develop core 2048 game mechanics using pygame"
    ],
    [
      "P0",
      "Design a clean and intuitive user interface"
    ],
    [
      "P1",
      "Implement score tracking with high score memory"
    ],
    [
      "P1",
      "Add undo move feature for enhanced gameplay strategy"
    ],
    [
      "P2",
      "Create visually appealing graphics and animations"
    ]
  ],
  "UI Design draft": "The UI will feature a minimalist design with a focus on ease of use. The main game screen will display the game grid, current score, high score, and an undo button. The color scheme will be consistent and pleasant to the eye, with smooth transitions for tile movements.",
  "Anything UNCLEAR": "The specifics of the undo feature need to be clarified, such as how many moves can be undone and whether it affects the scoring."
}

### Search Information
-
"""


@pytest.fixture()
def llm():
    return OpenAIGPTAPI()


@pytest.mark.asyncio
async def test_write_prd_an(llm):
    node = await REFINE_PRD_NODE.fill(CONTEXT, llm)
    assert node.instruct_content
    assert "Refined Requirement Pool" in node.instruct_content.json(ensure_ascii=False)
