#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : alexanderwu
@File    : write_review.py
"""
import asyncio
from typing import List, Literal

from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode

REVIEW = ActionNode(
    key="Review",
    expected_type=List[str],
    instruction="Act as an experienced reviewer and critically assess the given output. Provide specific and"
    " constructive feedback, highlighting areas for improvement and suggesting changes.",
    example=[
        "The logic in the function `calculate_total` seems flawed. Shouldn't it consider the discount rate as well?",
        "The TODO function is not implemented yet? Should we implement it before commit?",
    ],
)

REVIEW_RESULT = ActionNode(
    key="ReviewResult",
    expected_type=Literal["LGTM", "LBTM"],
    instruction="LGTM/LBTM. If the code is fully implemented, " "give a LGTM, otherwise provide a LBTM.",
    example="LBTM",
)

NEXT_STEPS = ActionNode(
    key="NextSteps",
    expected_type=str,
    instruction="Based on the code review outcome, suggest actionable steps. This can include code changes, "
    "refactoring suggestions, or any follow-up tasks.",
    example="""1. Refactor the `process_data` method to improve readability and efficiency.
2. Cover edge cases in the `validate_user` function.
3. Implement a the TODO in the `calculate_total` function.
4. Fix the `handle_events` method to update the game state only if a move is successful.
   ```python
   def handle_events(self):
       for event in pygame.event.get():
           if event.type == pygame.QUIT:
               return False
           if event.type == pygame.KEYDOWN:
               moved = False
               if event.key == pygame.K_UP:
                   moved = self.game.move('UP')
               elif event.key == pygame.K_DOWN:
                   moved = self.game.move('DOWN')
               elif event.key == pygame.K_LEFT:
                   moved = self.game.move('LEFT')
               elif event.key == pygame.K_RIGHT:
                   moved = self.game.move('RIGHT')
               if moved:
                   # Update the game state only if a move was successful
                   self.render()
       return True
   ```
""",
)

WRITE_DRAFT = ActionNode(
    key="WriteDraft",
    expected_type=str,
    instruction="Could you write draft code for move function in order to implement it?",
    example="Draft: ...",
)


WRITE_FUNCTION = ActionNode(
    key="WriteFunction",
    expected_type=str,
    instruction="write code for the function not implemented.",
    example="""
```Code
...
```
""",
)


REWRITE_CODE = ActionNode(
    key="RewriteCode",
    expected_type=str,
    instruction="""rewrite code based on the Review and Actions""",
    example="""
```python
## example.py
def calculate_total(price, quantity):
    total = price * quantity
```
""",
)


CODE_REVIEW_CONTEXT = """
# System
Role: You are a professional software engineer, and your main task is to review and revise the code. You need to ensure that the code conforms to the google-style standards, is elegantly designed and modularized, easy to read and maintain.
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.

# Context
## System Design
{"Implementation approach": "我们将使用HTML、CSS和JavaScript来实现这个单机的响应式2048游戏。为了确保游戏性能流畅和响应式设计，我们会选择使用Vue.js框架，因为它易于上手且适合构建交互式界面。我们还将使用localStorage来记录玩家的最高分。", "File list": ["index.html", "styles.css", "main.js", "game.js", "storage.js"], "Data structures and interfaces": "classDiagram\
    class Game {\
        -board Array\
        -score Number\
        -bestScore Number\
        +constructor()\
        +startGame()\
        +move(direction: String)\
        +getBoard() Array\
        +getScore() Number\
        +getBestScore() Number\
        +setBestScore(score: Number)\
    }\
    class Storage {\
        +getBestScore() Number\
        +setBestScore(score: Number)\
    }\
    class Main {\
        +init()\
        +bindEvents()\
    }\
    Game --> Storage : uses\
    Main --> Game : uses", "Program call flow": "sequenceDiagram\
    participant M as Main\
    participant G as Game\
    participant S as Storage\
    M->>G: init()\
    G->>S: getBestScore()\
    S-->>G: return bestScore\
    M->>G: bindEvents()\
    M->>G: startGame()\
    loop Game Loop\
        M->>G: move(direction)\
        G->>S: setBestScore(score)\
        S-->>G: return\
    end", "Anything UNCLEAR": "目前项目要求明确，没有不清楚的地方。"}

## Tasks
{"Required Python packages": ["无需Python包"], "Required Other language third-party packages": ["vue.js"], "Logic Analysis": [["index.html", "作为游戏的入口文件和主要的HTML结构"], ["styles.css", "包含所有的CSS样式，确保游戏界面美观"], ["main.js", "包含Main类，负责初始化游戏和绑定事件"], ["game.js", "包含Game类，负责游戏逻辑，如开始游戏、移动方块等"], ["storage.js", "包含Storage类，用于获取和设置玩家的最高分"]], "Task list": ["index.html", "styles.css", "storage.js", "game.js", "main.js"], "Full API spec": "", "Shared Knowledge": "\'game.js\' 包含游戏逻辑相关的函数，被 \'main.js\' 调用。", "Anything UNCLEAR": "目前项目要求明确，没有不清楚的地方。"}

## Code Files
----- index.html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2048游戏</title>
    <link rel="stylesheet" href="styles.css">
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js"></script>
</head>
<body>
    <div id="app">
        <h1>2048</h1>
        <div class="scores-container">
            <div class="score-container">
                <div class="score-header">分数</div>
                <div>{{ score }}</div>
            </div>
            <div class="best-container">
                <div class="best-header">最高分</div>
                <div>{{ bestScore }}</div>
            </div>
        </div>
        <div class="game-container">
            <div v-for="(row, rowIndex) in board" :key="rowIndex" class="grid-row">
                <div v-for="(cell, cellIndex) in row" :key="cellIndex" class="grid-cell" :class="\'number-cell-\' + cell">
                    {{ cell !== 0 ? cell : \'\' }}
                </div>
            </div>
        </div>
        <button @click="startGame" aria-label="开始新游戏">新游戏</button>
    </div>

    <script src="storage.js"></script>
    <script src="game.js"></script>
    <script src="main.js"></script>
    <script src="app.js"></script>
</body>
</html>

----- styles.css
/* styles.css */
body, html {
    margin: 0;
    padding: 0;
    font-family: \'Arial\', sans-serif;
}

#app {
    text-align: center;
    font-size: 18px;
    color: #776e65;
}

h1 {
    color: #776e65;
    font-size: 72px;
    font-weight: bold;
    margin: 20px 0;
}

.scores-container {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
}

.score-container, .best-container {
    background: #bbada0;
    padding: 10px;
    border-radius: 5px;
    margin: 0 10px;
    min-width: 100px;
    text-align: center;
}

.score-header, .best-header {
    color: #eee4da;
    font-size: 18px;
    margin-bottom: 5px;
}

.game-container {
    max-width: 500px;
    margin: 0 auto 20px;
    background: #bbada0;
    padding: 15px;
    border-radius: 10px;
    position: relative;
}

.grid-row {
    display: flex;
}

.grid-cell {
    background: #cdc1b4;
    width: 100px;
    height: 100px;
    margin: 5px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 35px;
    font-weight: bold;
    color: #776e65;
    border-radius: 3px;
}

/* Dynamic classes for different number cells */
.number-cell-2 {
    background: #eee4da;
}

.number-cell-4 {
    background: #ede0c8;
}

.number-cell-8 {
    background: #f2b179;
    color: #f9f6f2;
}

.number-cell-16 {
    background: #f59563;
    color: #f9f6f2;
}

.number-cell-32 {
    background: #f67c5f;
    color: #f9f6f2;
}

.number-cell-64 {
    background: #f65e3b;
    color: #f9f6f2;
}

.number-cell-128 {
    background: #edcf72;
    color: #f9f6f2;
}

.number-cell-256 {
    background: #edcc61;
    color: #f9f6f2;
}

.number-cell-512 {
    background: #edc850;
    color: #f9f6f2;
}

.number-cell-1024 {
    background: #edc53f;
    color: #f9f6f2;
}

.number-cell-2048 {
    background: #edc22e;
    color: #f9f6f2;
}

/* Larger numbers need smaller font sizes */
.number-cell-1024, .number-cell-2048 {
    font-size: 30px;
}

button {
    background-color: #8f7a66;
    color: #f9f6f2;
    border: none;
    border-radius: 3px;
    padding: 10px 20px;
    font-size: 18px;
    cursor: pointer;
    outline: none;
}

button:hover {
    background-color: #9f8b76;
}

----- storage.js
## storage.js
class Storage {
    // 获取最高分
    getBestScore() {
        // 尝试从localStorage中获取最高分，如果不存在则默认为0
        const bestScore = localStorage.getItem(\'bestScore\');
        return bestScore ? Number(bestScore) : 0;
    }

    // 设置最高分
    setBestScore(score) {
        // 将最高分设置到localStorage中
        localStorage.setItem(\'bestScore\', score.toString());
    }
}



## Code to be Reviewed: game.js
```Code
## game.js
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


CODE_REVIEW_SMALLEST_CONTEXT = """
## Code to be Reviewed: game.js
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


CODE_REVIEW_SAMPLE = """
## Code Review: game.js
1. The code partially implements the requirements. The `Game` class is missing the full implementation of the `move` method, which is crucial for the game\'s functionality.
2. The code logic is not completely correct. The `move` method is not implemented, which means the game cannot process player moves.
3. The existing code follows the "Data structures and interfaces" in terms of class structure but lacks full method implementations.
4. Not all functions are implemented. The `move` method is incomplete and does not handle the logic for moving and merging tiles.
5. All necessary pre-dependencies seem to be imported since the code does not indicate the need for additional imports.
6. The methods from other files (such as `Storage`) are not being used in the provided code snippet, but the class structure suggests that they will be used correctly.

## Actions
1. Implement the `move` method to handle tile movements and merging. This is a complex task that requires careful consideration of the game\'s rules and logic. Here is a simplified version of how one might begin to implement the `move` method:
   ```javascript
   move(direction) {
       // Simplified logic for moving tiles up
       if (direction === \'up\') {
           for (let col = 0; col < 4; col++) {
               let tiles = this.board.map(row => row[col]).filter(val => val !== 0);
               let merged = [];
               for (let i = 0; i < tiles.length; i++) {
                   if (tiles[i] === tiles[i + 1]) {
                       tiles[i] *= 2;
                       this.score += tiles[i];
                       tiles[i + 1] = 0;
                       merged.push(i);
                   }
               }
               tiles = tiles.filter(val => val !== 0);
               while (tiles.length < 4) {
                   tiles.push(0);
               }
               for (let row = 0; row < 4; row++) {
                   this.board[row][col] = tiles[row];
               }
           }
       }
       // Additional logic needed for \'down\', \'left\', \'right\'
       // ...
       this.addRandomTile();
   }
   ```
2. Integrate the `Storage` class methods to handle the best score. This means updating the `startGame` and `setBestScore` methods to use `Storage` for retrieving and setting the best score:
   ```javascript
   startGame() {
       this.board = this.createEmptyBoard();
       this.score = 0;
       this.bestScore = new Storage().getBestScore(); // Retrieve the best score from storage
       this.addRandomTile();
       this.addRandomTile();
   }

   setBestScore(score) {
       if (score > this.bestScore) {
           this.bestScore = score;
           new Storage().setBestScore(score); // Set the new best score in storage
       }
   }
   ```

## Code Review Result
LBTM

```
"""


WRITE_CODE_NODE = ActionNode.from_children("WRITE_REVIEW_NODE", [REVIEW, REVIEW_RESULT, NEXT_STEPS])
WRITE_MOVE_NODE = ActionNode.from_children("WRITE_MOVE_NODE", [WRITE_DRAFT, WRITE_FUNCTION])


CR_FOR_MOVE_FUNCTION_BY_3 = """
The move function implementation provided appears to be well-structured and follows a clear logic for moving and merging tiles in the specified direction. However, there are a few potential improvements that could be made to enhance the code:

1. Encapsulation: The logic for moving and merging tiles could be encapsulated into smaller, reusable functions to improve readability and maintainability.

2. Magic Numbers: There are some magic numbers (e.g., 4, 3) used in the loops that could be replaced with named constants for improved readability and easier maintenance.

3. Comments: Adding comments to explain the logic and purpose of each section of the code can improve understanding for future developers who may need to work on or maintain the code.

4. Error Handling: It's important to consider error handling for unexpected input or edge cases to ensure the function behaves as expected in all scenarios.

Overall, the code could benefit from refactoring to improve readability, maintainability, and extensibility. If you would like, I can provide a refactored version of the move function that addresses these considerations.
"""


class WriteCodeAN(Action):
    """Write a code review for the context."""

    async def run(self, context):
        self.llm.system_prompt = "You are an outstanding engineer and can implement any code"
        return await WRITE_MOVE_NODE.fill(context=context, llm=self.llm, schema="json")


async def main():
    await WriteCodeAN().run(CODE_REVIEW_SMALLEST_CONTEXT)


if __name__ == "__main__":
    asyncio.run(main())
