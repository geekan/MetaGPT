#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : test_llm.py
"""

import pytest

from metagpt.llm import LLM

CODE_REVIEW_SMALLEST_CONTEXT = """
## game.js
```Code
// game.js
class Game {
    constructor() {
        this.board = this.createEmptyBoard();
        this.score = 0;
        this.bestScore = 0;
    }

    createEmptyBoard() {
        const board = [];
        for (let i = 0; i < 4; i++) {
            board[i] = [0, 0, 0, 0];
        }
        return board;
    }

    startGame() {
        this.board = this.createEmptyBoard();
        this.score = 0;
        this.addRandomTile();
        this.addRandomTile();
    }

    addRandomTile() {
        let emptyCells = [];
        for (let r = 0; r < 4; r++) {
            for (let c = 0; c < 4; c++) {
                if (this.board[r][c] === 0) {
                    emptyCells.push({ r, c });
                }
            }
        }
        if (emptyCells.length > 0) {
            let randomCell = emptyCells[Math.floor(Math.random() * emptyCells.length)];
            this.board[randomCell.r][randomCell.c] = Math.random() < 0.9 ? 2 : 4;
        }
    }

    move(direction) {
        // This function will handle the logic for moving tiles
        // in the specified direction and merging them
        // It will also update the score and add a new random tile if the move is successful
        // The actual implementation of this function is complex and would require
        // a significant amount of code to handle all the cases for moving and merging tiles
        // For the purposes of this example, we will not implement the full logic
        // Instead, we will just call addRandomTile to simulate a move
        this.addRandomTile();
    }

    getBoard() {
        return this.board;
    }

    getScore() {
        return this.score;
    }

    getBestScore() {
        return this.bestScore;
    }

    setBestScore(score) {
        this.bestScore = score;
    }
}

```
"""

MOVE_DRAFT = """
## move function draft

```javascript
move(direction) {
    let moved = false;
    switch (direction) {
        case 'up':
            for (let c = 0; c < 4; c++) {
                for (let r = 1; r < 4; r++) {
                    if (this.board[r][c] !== 0) {
                        let row = r;
                        while (row > 0 && this.board[row - 1][c] === 0) {
                            this.board[row - 1][c] = this.board[row][c];
                            this.board[row][c] = 0;
                            row--;
                            moved = true;
                        }
                        if (row > 0 && this.board[row - 1][c] === this.board[row][c]) {
                            this.board[row - 1][c] *= 2;
                            this.board[row][c] = 0;
                            this.score += this.board[row - 1][c];
                            moved = true;
                        }
                    }
                }
            }
            break;
        case 'down':
            // Implement logic for moving tiles down
            // Similar to the 'up' case but iterating in reverse order
            // and checking for merging in the opposite direction
            break;
        case 'left':
            // Implement logic for moving tiles left
            // Similar to the 'up' case but iterating over columns first
            // and checking for merging in the opposite direction
            break;
        case 'right':
            // Implement logic for moving tiles right
            // Similar to the 'up' case but iterating over columns in reverse order
            // and checking for merging in the opposite direction
            break;
    }

    if (moved) {
        this.addRandomTile();
    }
}
```
"""

FUNCTION_TO_MERMAID_CLASS = """
## context
```
class UIDesign(Action):
    #Class representing the UI Design action.
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)  # 需要调用LLM进一步丰富UI设计的prompt
    @parse
    def parse_requirement(self, context: str):
        #Parse UI Design draft from the context using regex.
        pattern = r"## UI Design draft.*?\n(.*?)## Anything UNCLEAR"
        return context, pattern
    @parse
    def parse_ui_elements(self, context: str):
        #Parse Selected Elements from the context using regex.
        pattern = r"## Selected Elements.*?\n(.*?)## HTML Layout"
        return context, pattern
    @parse
    def parse_css_code(self, context: str):
        pattern = r"```css.*?\n(.*?)## Anything UNCLEAR"
        return context, pattern
    @parse
    def parse_html_code(self, context: str):
        pattern = r"```html.*?\n(.*?)```"
        return context, pattern
    async def draw_icons(self, context, *args, **kwargs):
        #Draw icons using SDEngine.
        engine = SDEngine()
        icon_prompts = self.parse_ui_elements(context)
        icons = icon_prompts.split("\n")
        icons = [s for s in icons if len(s.strip()) > 0]
        prompts_batch = []
        for icon_prompt in icons:
            # fixme: 添加icon lora
            prompt = engine.construct_payload(icon_prompt + ".<lora:WZ0710_AW81e-3_30e3b128d64T32_goon0.5>")
            prompts_batch.append(prompt)
        await engine.run_t2i(prompts_batch)
        logger.info("Finish icon design using StableDiffusion API")
    async def _save(self, css_content, html_content):
        save_dir = CONFIG.workspace_path / "resources" / "codes"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        # Save CSS and HTML content to files
        css_file_path = save_dir / "ui_design.css"
        html_file_path = save_dir / "ui_design.html"
        with open(css_file_path, "w") as css_file:
            css_file.write(css_content)
        with open(html_file_path, "w") as html_file:
            html_file.write(html_content)
    async def run(self, requirements: list[Message], *args, **kwargs) -> ActionOutput:
        #Run the UI Design action.
        # fixme: update prompt (根据需求细化prompt）
        context = requirements[-1].content
        ui_design_draft = self.parse_requirement(context=context)
        # todo: parse requirements str
        prompt = PROMPT_TEMPLATE.format(context=ui_design_draft, format_example=FORMAT_EXAMPLE)
        logger.info(prompt)
        ui_describe = await self._aask_v1(prompt, "ui_design", OUTPUT_MAPPING)
        logger.info(ui_describe.content)
        logger.info(ui_describe.instruct_content)
        css = self.parse_css_code(context=ui_describe.content)
        html = self.parse_html_code(context=ui_describe.content)
        await self._save(css_content=css, html_content=html)
        await self.draw_icons(ui_describe.content)
        return ui_describe
```
-----
## format example
[CONTENT]
{
    "ClassView": "classDiagram\n        class A {\n        -int x\n        +int y\n        -int speed\n        -int direction\n        +__init__(x: int, y: int, speed: int, direction: int)\n        +change_direction(new_direction: int) None\n        +move() None\n    }\n    "
}
[/CONTENT]
## nodes: "<node>: <type>  # <comment>"
- ClassView: <class 'str'>  # Generate the mermaid class diagram corresponding to source code in "context."
## constraint
- Language: Please use the same language as the user input.
- Format: output wrapped inside [CONTENT][/CONTENT] as format example, nothing else.
## action
Fill in the above nodes(ClassView) based on the format example.
"""

MOVE_FUNCTION = """
## move function implementation

```javascript
move(direction) {
    let moved = false;
    switch (direction) {
        case 'up':
            for (let c = 0; c < 4; c++) {
                for (let r = 1; r < 4; r++) {
                    if (this.board[r][c] !== 0) {
                        let row = r;
                        while (row > 0 && this.board[row - 1][c] === 0) {
                            this.board[row - 1][c] = this.board[row][c];
                            this.board[row][c] = 0;
                            row--;
                            moved = true;
                        }
                        if (row > 0 && this.board[row - 1][c] === this.board[row][c]) {
                            this.board[row - 1][c] *= 2;
                            this.board[row][c] = 0;
                            this.score += this.board[row - 1][c];
                            moved = true;
                        }
                    }
                }
            }
            break;
        case 'down':
            for (let c = 0; c < 4; c++) {
                for (let r = 2; r >= 0; r--) {
                    if (this.board[r][c] !== 0) {
                        let row = r;
                        while (row < 3 && this.board[row + 1][c] === 0) {
                            this.board[row + 1][c] = this.board[row][c];
                            this.board[row][c] = 0;
                            row++;
                            moved = true;
                        }
                        if (row < 3 && this.board[row + 1][c] === this.board[row][c]) {
                            this.board[row + 1][c] *= 2;
                            this.board[row][c] = 0;
                            this.score += this.board[row + 1][c];
                            moved = true;
                        }
                    }
                }
            }
            break;
        case 'left':
            for (let r = 0; r < 4; r++) {
                for (let c = 1; c < 4; c++) {
                    if (this.board[r][c] !== 0) {
                        let col = c;
                        while (col > 0 && this.board[r][col - 1] === 0) {
                            this.board[r][col - 1] = this.board[r][col];
                            this.board[r][col] = 0;
                            col--;
                            moved = true;
                        }
                        if (col > 0 && this.board[r][col - 1] === this.board[r][col]) {
                            this.board[r][col - 1] *= 2;
                            this.board[r][col] = 0;
                            this.score += this.board[r][col - 1];
                            moved = true;
                        }
                    }
                }
            }
            break;
        case 'right':
            for (let r = 0; r < 4; r++) {
                for (let c = 2; c >= 0; c--) {
                    if (this.board[r][c] !== 0) {
                        let col = c;
                        while (col < 3 && this.board[r][col + 1] === 0) {
                            this.board[r][col + 1] = this.board[r][col];
                            this.board[r][col] = 0;
                            col++;
                            moved = true;
                        }
                        if (col < 3 && this.board[r][col + 1] === this.board[r][col]) {
                            this.board[r][col + 1] *= 2;
                            this.board[r][col] = 0;
                            this.score += this.board[r][col + 1];
                            moved = true;
                        }
                    }
                }
            }
            break;
    }

    if (moved) {
        this.addRandomTile();
    }
}
```
"""


@pytest.fixture()
def llm():
    return LLM()


@pytest.mark.asyncio
async def test_llm_code_review(llm):
    choices = [
        "Please review the move function code above. Should it be refactor?",
        "Please implement the move function",
        "Please write a draft for the move function in order to implement it",
    ]
    # prompt = CODE_REVIEW_SMALLEST_CONTEXT+ "\n\n" + MOVE_DRAFT + "\n\n" + choices[1]
    # rsp = await llm.aask(prompt)

    prompt = CODE_REVIEW_SMALLEST_CONTEXT + "\n\n" + MOVE_FUNCTION + "\n\n" + choices[0]
    prompt = FUNCTION_TO_MERMAID_CLASS

    _ = await llm.aask(prompt)


# if __name__ == "__main__":
#     pytest.main([__file__, "-s"])
