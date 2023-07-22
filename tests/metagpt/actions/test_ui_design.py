# -*- coding: utf-8 -*-
# @Date    : 2023/7/22 02:40
# @Author  : stellahong (stellahong@fuzhi.ai)
#
from tests.metagpt.roles.ui_role import UIDesign

llm_resp= '''
    # UI Design Description
```The user interface for the snake game will be designed in a way that is simple, clean, and intuitive. The main elements of the game such as the game grid, snake, food, score, and game over message will be clearly defined and easy to understand. The game grid will be centered on the screen with the score displayed at the top. The game controls will be intuitive and easy to use. The design will be modern and minimalist with a pleasing color scheme.```

## Selected Elements

Game Grid: The game grid will be a rectangular area in the center of the screen where the game will take place. It will be defined by a border and will have a darker background color.

Snake: The snake will be represented by a series of connected blocks that move across the grid. The color of the snake will be different from the background color to make it stand out.

Food: The food will be represented by small objects that are a different color from the snake and the background. The food will be randomly placed on the grid.

Score: The score will be displayed at the top of the screen. The score will increase each time the snake eats a piece of food.

Game Over: When the game is over, a message will be displayed in the center of the screen. The player will be given the option to restart the game.

## HTML Layout
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snake Game</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="score">Score: 0</div>
    <div class="game-grid">
        <!-- Snake and food will be dynamically generated here using JavaScript -->
    </div>
    <div class="game-over">Game Over</div>
</body>
</html>
```

## CSS Styles (styles.css)
```css
body {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
    background-color: #f0f0f0;
}

.score {
    font-size: 2em;
    margin-bottom: 1em;
}

.game-grid {
    width: 400px;
    height: 400px;
    display: grid;
    grid-template-columns: repeat(20, 1fr);
    grid-template-rows: repeat(20, 1fr);
    gap: 1px;
    background-color: #222;
    border: 1px solid #555;
}

.snake-segment {
    background-color: #00cc66;
}

.food {
    background-color: #cc3300;
}

.control-panel {
    display: flex;
    justify-content: space-around;
    width: 400px;
    margin-top: 1em;
}

.control-button {
    padding: 1em;
    font-size: 1em;
    border: none;
    background-color: #555;
    color: #fff;
    cursor: pointer;
}

.game-over {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 3em;
    '''

def test_ui_design_parse_css():
    ui_design_work = UIDesign(name="UI design action")

    css = '''
    body {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
    background-color: #f0f0f0;
}

.score {
    font-size: 2em;
    margin-bottom: 1em;
}

.game-grid {
    width: 400px;
    height: 400px;
    display: grid;
    grid-template-columns: repeat(20, 1fr);
    grid-template-rows: repeat(20, 1fr);
    gap: 1px;
    background-color: #222;
    border: 1px solid #555;
}

.snake-segment {
    background-color: #00cc66;
}

.food {
    background-color: #cc3300;
}

.control-panel {
    display: flex;
    justify-content: space-around;
    width: 400px;
    margin-top: 1em;
}

.control-button {
    padding: 1em;
    font-size: 1em;
    border: none;
    background-color: #555;
    color: #fff;
    cursor: pointer;
}

.game-over {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 3em;
    '''
    assert ui_design_work.parse_css_code(context=llm_resp)==css


def test_ui_design_parse_html():
    ui_design_work = UIDesign(name="UI design action")

    html = '''
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snake Game</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="score">Score: 0</div>
    <div class="game-grid">
        <!-- Snake and food will be dynamically generated here using JavaScript -->
    </div>
    <div class="game-over">Game Over</div>
</body>
</html>
    '''
    assert ui_design_work.parse_css_code(context=llm_resp)==html



