#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import pytest

from metagpt.actions.intent_detect import IntentDetect, LightIntentDetect
from metagpt.logs import logger
from metagpt.schema import Message

DEMO_CONTENT = [
    {
        "role": "user",
        "content": "Can you build TextToSummarize which is a SMS number that I can text and it will scrape a website "
        "and summarize it with ChatGPT",
    },
    {
        "role": "assistant",
        "content": "Absolutely, I can build a service like TextToSummarize for you. The process will involve setting up"
        " an SMS service that can receive your texts, scraping the website content you send, and then using"
        " an AI to summarize the content.\nTo get started, I'll need to set up a number for receiving SMS"
        ", then I'll work on the script to scrape the website content from the URLs you text, and finally."
        " I'll integrate it with an AI service to Generalte the summaries.\n I'll keep you updated on my"
        " progress!",
    },
    {"role": "user", "content": "What exactly do we need the web app for?"},
    {
        "role": "assistant",
        "content": "The web app will service as the interface between the SMS service and the AI summarization service"
        ". When you send a text with a URL to the SMS number, teh web app will process that, scrape the"
        " content from the URL, and then use the AI to summarize it. The summary will then be sent back to"
        " you. It's the central hub that ties all the components of the service togather.",
    },
]

DEMO1_CONTENT = [
    {
        "role": "user",
        "content": "Extract all of the blog posts from `https://stripe.com/blog/page/1` and return a CSV with the"
        " columns `date`, `article_text`, `author` and `summary`. Generate a summary for each article"
        " yourself.",
    }
]

_DEMO2_CONTENT_ASSISTANT = """
user: 
## User Requirement
### User Requirement Detail
```text
2048 game
````
### Knowledge
To meet user requirements, the following standard operating procedure(SOP) must be used. SOP descriptions cannot be modified; user requirements can only be appended to the end of corresponding steps.
- Writes a PRD based on software requirements.
- Writes a design to the project repository, based on the PRD of the project.
- Writes a project plan to the project repository, based on the design of the project.
- Writes code to implement designed features according to the project plan and adds them to the project repository.
- Stage and commit changes for the project repository using Git.
## Context

## Current Plan
[
    {
        "task_id": "1",
        "dependent_task_ids": [],
        "instruction": "Write a PRD based on the software requirements.",
        "task_type": "other",
        "code": "from metagpt.tools.libs.software_development import write_prd\n\nasync def create_2048_game_prd():\n    idea = \"Create a 2048 game\"\n    prd_path = await write_prd(idea)\n    return prd_path\n\nawait create_2048_game_prd()\n",
        "result": ",,,,,[,CONTENT]\n{\n    \"Language\": \"en_us\",\n    \"Programming Language\": \"Python\",\n    \"Original Requirements\": \"Create a, 2048 game\",\n    \"Project Name\": \"game_2048\",\n    \"Product Goals\": [\n        \"Create an engaging user experience\",\n       , \"Improve accessibility, be responsive\",\n        \"More beautiful UI\"\n    ],\n    \"User Stories\": [\n        \",As a player, I want to be able to choose difficulty levels\",\n        \"As a player,, I want to see my score after each game\",\n        \"As a player, I want, to get restart button when I lose\",\n        \"As a player, I want to see beautiful UI that make me feel good\",\n        \"As a player, I want to play game via mobile phone\"\n   , ],\n    \"Competitive Analysis\": [\n        \"2048 Game, A: Simple interface, lacks responsive features\",\n        \"play2048.co: Beautiful and responsive UI with my best score shown\",\n        \"2048game.com: Responsive UI with my, best score shown, but many ads\"\n    ],\n    \"Competitive Quadrant, Chart\": \"quadrantChart\\n    title, \\\"Reach and engagement of campaigns\\\"\\n    x-axis \\\"Low Reach\\\" --> \\\"High Reach\\\"\\n    y-axis \\\"Low Engagement\\\" --> \\\",High Engagement\\\"\\n    quadrant-1 \\\"We should expand\\\"\\n    quadrant-2 \\\"Need to promote\\\"\\n    quadrant,-3 \\\"Re-evaluate\\\"\\n    quadrant-4 \\\"May be, improved\\\"\\n    \\\"Campaign A\\\": [0.3, 0.6]\\n    \\\"Campaign B\\\": [0.45, 0.,23]\\n    \\\"Campaign C\\\": [0.57, 0.69]\\n    \\\"Campaign D\\\": [0.78, 0.34]\\n   , \\\"Campaign E\\\": [0.40, 0.34]\\n    \\\"Campaign, F\\\": [0.35, 0.78]\\n    \\\"Our Target Product\\\": [0.5, 0.6,]\",\n    \"Requirement Analysis\": \"\",\n    \"Requirement Pool\": [\n        [\n            \"P0\",\n,            \"The main code ...\"\n        ],\n        [\n            \"P0\",\n            \"The game algorithm ...\"\n        ]\n,    ],\n    \"UI Design draft\": \"Basic function description with a simple style and layout.\",\n    \"Anything UNCLEAR,\": \"\"\n}\n[/CONTENT]\n,,,,,,,,,,,,{'output': '[{\"type_\": \"str\", \"name\": \"PRD File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/prd/20240401194850.json\"}, {\"type_\": \"str\", \"name\": \"Competitive Analysis\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/competitive_analysis/20240401194850.mmd\"}, {\"type_\": \"str\", \"name\": \"Competitive Analysis\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/competitive_analysis/20240401194850.pdf\"}, {\"type_\": \"str\", \"name\": \"Competitive Analysis\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/competitive_analysis/20240401194850.png\"}, {\"type_\": \"str\", \"name\": \"Competitive Analysis\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/competitive_analysis/20240401194850.svg\"}]', 'tool_name': 'write_prd'},PosixPath('/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/prd')",
        "is_success": true,
        "is_finished": true
    },
    {
        "task_id": "2",
        "dependent_task_ids": [
            "1"
        ],
        "instruction": "Write a design to the project repository, based on the PRD of the project.",
        "task_type": "other",
        "code": "from metagpt.tools.libs.software_development import write_design\n\nasync def create_2048_game_design(prd_path):\n    system_design_path = await write_design(prd_path)\n    return system_design_path\n\nawait create_2048_game_design('/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/prd/20240401194850.json')\n",
        "result": ",[CONTENT]\n{\n    \"Implementation approach\":, \"We will use the Py,game library to create the game interface and handle user input. The game logic will be implemented using Python classes and data structures to manage the game, board and tiles.\",\n    \"File list\": [\n        \"main.py,\",\n        \"game.py\"\n,    ],\n    \"Data structures and interfaces\": \"\\nclassDiagram\\n    class Game2048 {\\n        -int[][] board,\\n        -int score\\n        -bool game_over\\n        +__init__()\\n        +reset()\\n        +,move(direction: str)\\n        +get_board() int[][]\\n        +get_score() int\\n        +is_game_over() bool\\n    }\\n   , class UI {\\n        +display_board(board: int[][], score: int)\\n,        +show_game_over()\\n    }\\n    Game,2048 --> UI\\n\",\n    \"Program call flow\": \"\\nsequenceDiagram,\\n    participant M as Main\\n    participant G as Game2048,\\n    participant UI as UI\\n    M->>G: reset,()\\n    G-->>UI: display_board(board, score)\\,n    M->>G: move(direction)\\n    G-->>,G: update board and score\\n    G-->>UI:, display_board(board, score)\\n    G->>G: is_game_over,()\\n    G-->>UI: show_game_over()\\n\",\n,,,,,    \"Anything UNCLEAR\": \"\"\n}\n[/CONTENT]\n,,,,,,,,,,,,,,,{'output': '[{\"type_\": \"str\", \"name\": \"Intermedia Design File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/system_design/20240401194850.json\"}, {\"type_\": \"str\", \"name\": \"Design File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/system_design/20240401194850.md\"}, {\"type_\": \"str\", \"name\": \"Class Diagram File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/data_api_design/20240401194850.mmd\"}, {\"type_\": \"str\", \"name\": \"Class Diagram File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/data_api_design/20240401194850.pdf\"}, {\"type_\": \"str\", \"name\": \"Class Diagram File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/data_api_design/20240401194850.png\"}, {\"type_\": \"str\", \"name\": \"Class Diagram File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/data_api_design/20240401194850.svg\"}, {\"type_\": \"str\", \"name\": \"Sequence Diagram File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/seq_flow/20240401194850.mmd\"}, {\"type_\": \"str\", \"name\": \"Sequence Diagram File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/seq_flow/20240401194850.pdf\"}, {\"type_\": \"str\", \"name\": \"Sequence Diagram File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/seq_flow/20240401194850.png\"}, {\"type_\": \"str\", \"name\": \"Sequence Diagram File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/resources/seq_flow/20240401194850.svg\"}]', 'tool_name': 'write_design'},PosixPath('/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/system_design')",
        "is_success": true,
        "is_finished": true
    },
    {
        "task_id": "3",
        "dependent_task_ids": [
            "2"
        ],
        "instruction": "Write a project plan to the project repository, based on the design of the project.",
        "task_type": "other",
        "code": "from metagpt.tools.libs.software_development import write_project_plan\n\nasync def create_2048_game_project_plan(system_design_path):\n    task_path = await write_project_plan(system_design_path)\n    return task_path\n\nawait create_2048_game_project_plan('/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/system_design/20240401194850.json')\n",
        "result": ",\n[CONTENT,]\n{\n    \"Required Python packages\": [\n        \"pygame==2.0.1\"\n    ],\n    \"Required, Other language third-party packages\": [\n        \"No third-party dependencies required,\"\n    ],\n    \"Logic Analysis\": [\n       , [\n            \"game.py\",\n            \"Contains Game2048, class and functions to manage the game board and tiles\"\n,        ],\n        [\n            \"main.py\",\n            \",Contains the main function, and imports Game2048, from game.py\"\n        ]\n    ],\n    \"Task list,\": [\n        \"game.py\",\n        \"main.py\"\n,    ],\n    \"Full API spec\":, \"\",\n    \"Shared Knowledge\": \"The Pygame library will be used, to create the game interface and handle user input. The game, logic will be implemented using Python classes and data structures to manage the game, board and tiles.\",\n    \"Anything UNCLEAR\": \"No unclear aspects,,,,, mentioned.\"\n}\n[/CONTENT]\n{'output': '[{\"type_\": \"str\", \"name\": \"Project Plan\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/task/20240401194850.json\"}]', 'tool_name': 'write_project_plan'},PosixPath('/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/task')",
        "is_success": true,
        "is_finished": true
    },
    {
        "task_id": "4",
        "dependent_task_ids": [
            "3"
        ],
        "instruction": "Write code to implement designed features according to the project plan and add them to the project repository.",
        "task_type": "other",
        "code": "from metagpt.tools.libs.software_development import write_codes\n\nasync def implement_2048_game_features(task_path):\n    src_path = await write_codes(task_path)\n    return src_path\n\nawait implement_2048_game_features('/Users/iorishinier/github/MetaGPT/workspace/game_2048/docs/task/20240401194850.json')\n",
        "result": ",```python\n,## game.py\n\nclass Game2048,:\n    def __init__(self):\n,        self.board = [[0 for _, in range(4)] for _ in, range(4)]\n        self.score =, 0\n        self.game_over =, False\n\n    def reset(self):\n       , self.board = [[0 for _ in, range(4)] for _, in range(4)]\n        self.score = 0\n        self,.game_over = False\n\n   , def move(self, direction: str):\n,        # Implement the logic to move the, tiles in the specified direction\n,        pass\n\n    def get_board(self) ->, list:\n        return self.board\n\n   , def get_score(self) -> int:\n,        return self.score\n\n    def is,_game_over(self) -> bool:\n       ,,,,, return self.game_over\n```\n,```,python\n## main.py\n\nimport pygame\nfrom game import Game2048\n\ndef main():\n    # Initialize the game\n    game = Game2048()\n    game.reset()\n\n    # Initialize Pygame\n,    pygame.init()\n    screen = pygame.display.set_mode((400, 400))\n    pygame.display.set_caption('2048 Game,')\n\n    running = True\n    while running:\n        for event in pygame.event.get():\n            if, event.type == pygame.QUIT:\n                running = False\n            elif event.type == pygame.KEYDOWN:\n                if event.key ==, pygame.K_UP:\n                    game.move('up')\n                elif event.key == pygame.K_DOWN:\n                   , game.move('down')\n                elif event.key == pygame.K_LEFT:\n                    game.move('left')\n                elif, event.key == pygame.K_RIGHT,:\n                    game.move('right')\n\n        # Display the game board and score\n        board = game.get_board()\n        score = game.get_score()\n        display_board(screen, board, score)\n\n        # Check, if the game is over\n        if game.is_game_over():\n            show_game_over(screen)\n\n        pygame.display.update()\n\n    pygame.quit()\n\n,def display_board(screen, board, score):\n    # Write,,,, code to display the game board and score on the Pygame screen\n    pass\n\ndef show_game_over(screen):\n    # Write code to display the game over message on the Pygame screen\n    pass\n\nif __name__ == \"__main__\":\n    main()\n```\n,,{'output': '[{\"type_\": \"str\", \"name\": \"Source File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/game_2048/__init__.py\"}, {\"type_\": \"str\", \"name\": \"Source File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/game_2048/game.py\"}, {\"type_\": \"str\", \"name\": \"Source File\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048/game_2048/main.py\"}]', 'tool_name': 'write_codes'},PosixPath('/Users/iorishinier/github/MetaGPT/workspace/game_2048/game_2048')",
        "is_success": true,
        "is_finished": true
    },
    {
        "task_id": "5",
        "dependent_task_ids": [
            "4"
        ],
        "instruction": "Stage and commit changes for the project repository using Git.",
        "task_type": "other",
        "code": "from metagpt.tools.libs.software_development import git_archive\n\nproject_path = '/Users/iorishinier/github/MetaGPT/workspace/game_2048'\ngit_log = await git_archive(project_path)\nprint(git_log)\n",
        "result": ",{'output': '[{\"type_\": \"str\", \"name\": \"Git Commit\", \"value\": \"/Users/iorishinier/github/MetaGPT/workspace/game_2048\"}]', 'tool_name': 'git_archive'}commit 41c731341d0da8b630709bca50d4841dcea98d43\nAuthor: 莘权 马 <mashenquan@fuzhi.ai>\nDate:   Mon Apr 1 19:50:53 2024 +0800\n\n    Archive\n\ncommit a61daa93f24e74bf934ea5a3ba217038f167ab1f\nAuthor: 莘权 马 <mashenquan@fuzhi.ai>\nDate:   Mon Apr 1 19:48:40 2024 +0800\n\n    Add .gitignore\n",
        "is_success": true,
        "is_finished": true
    }
]
## Current Task
{}

"""

DEMO2_CONTENT = [
    {"role": "user", "content": 'Create a "2048 game"'},
    {"role": "assistant", "content": _DEMO2_CONTENT_ASSISTANT},
    {"role": "user", "content": "TypeError: __init__() takes 1 positional argument but 2 were given"},
]

DEMO3_CONTENT = [
    {"role": "user", "content": "git clone 'https://github.com/spec-first/connexion' and format to MetaGPT project"}
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [json.dumps(DEMO1_CONTENT), json.dumps(DEMO_CONTENT), json.dumps(DEMO2_CONTENT), json.dumps(DEMO3_CONTENT)],
)
async def test_intent_detect(content: str, context):
    action = IntentDetect(context=context)
    messages = [Message.model_validate(i) for i in json.loads(content)]
    rsp = await action.run(messages)
    assert isinstance(rsp, Message)
    assert action._dialog_intentions
    assert action._references
    assert action._intent_to_sops
    assert action.result
    logger.info(action.result.model_dump_json())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [json.dumps(DEMO1_CONTENT), json.dumps(DEMO_CONTENT), json.dumps(DEMO2_CONTENT), json.dumps(DEMO3_CONTENT)],
)
async def test_light_intent_detect(content: str, context):
    action = LightIntentDetect(context=context)
    messages = [Message.model_validate(i) for i in json.loads(content)]
    rsp = await action.run(messages)
    assert isinstance(rsp, Message)
    assert action._dialog_intentions
    assert action._intent_to_sops
    assert action.result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
