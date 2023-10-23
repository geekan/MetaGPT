# -*- coding: utf-8 -*-
# @Date    : 2023/7/15 16:40
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import os
import re
from functools import wraps
from importlib import import_module

from metagpt.actions import Action, ActionOutput, WritePRD
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.tools.sd_engine import SDEngine

PROMPT_TEMPLATE = """
# Context
{context}

## Format example
{format_example}
-----
Role: You are a UserInterface Designer; the goal is to finish a UI design according to PRD, give a design description, and select specified elements and UI style.
Requirements: Based on the context, fill in the following missing information, provide detailed HTML and CSS code
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## UI Design Description:Provide as Plain text, place the design objective here
## Selected Elements:Provide as Plain text, up to 5 specified elements, clear and simple
## HTML Layout:Provide as Plain text, use standard HTML code
## CSS Styles (styles.css):Provide as Plain text,use standard css code
## Anything UNCLEAR:Provide as Plain text. Make clear here.

"""

FORMAT_EXAMPLE = """

## UI Design Description
```Snake games are classic and addictive games with simple yet engaging elements. Here are the main elements commonly found in snake games ```

## Selected Elements

Game Grid: The game grid is a rectangular...

Snake: The player controls a snake that moves across the grid...

Food: Food items (often represented as small objects or differently colored blocks)

Score: The player's score increases each time the snake eats a piece of food. The longer the snake becomes, the higher the score.

Game Over: The game ends when the snake collides with itself or an obstacle. At this point, the player's final score is displayed, and they are given the option to restart the game.


## HTML Layout
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snake Game</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="game-grid">
        <!-- Snake will be dynamically generated here using JavaScript -->
    </div>
    <div class="food">
        <!-- Food will be dynamically generated here using JavaScript -->
    </div>
</body>
</html>

## CSS Styles (styles.css)
body {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
    background-color: #f0f0f0;
}

.game-grid {
    width: 400px;
    height: 400px;
    display: grid;
    grid-template-columns: repeat(20, 1fr); /* Adjust to the desired grid size */
    grid-template-rows: repeat(20, 1fr);
    gap: 1px;
    background-color: #222;
    border: 1px solid #555;
}

.game-grid div {
    width: 100%;
    height: 100%;
    background-color: #444;
}

.snake-segment {
    background-color: #00cc66; /* Snake color */
}

.food {
    width: 100%;
    height: 100%;
    background-color: #cc3300; /* Food color */
    position: absolute;
}

/* Optional styles for a simple game over message */
.game-over {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 24px;
    font-weight: bold;
    color: #ff0000;
    display: none;
}

## Anything UNCLEAR
There are no unclear points.

"""

OUTPUT_MAPPING = {
    "UI Design Description": (str, ...),
    "Selected Elements": (str, ...),
    "HTML Layout": (str, ...),
    "CSS Styles (styles.css)": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


def load_engine(func):
    """Decorator to load an engine by file name and engine name."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        file_name, engine_name = func(*args, **kwargs)
        engine_file = import_module(file_name, package="metagpt")
        ip_module_cls = getattr(engine_file, engine_name)
        try:
            engine = ip_module_cls()
        except:
            engine = None

        return engine

    return wrapper


def parse(func):
    """Decorator to parse information using regex pattern."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        context, pattern = func(*args, **kwargs)
        match = re.search(pattern, context, re.DOTALL)
        if match:
            text_info = match.group(1)
            logger.info(text_info)
        else:
            text_info = context
            logger.info("未找到匹配的内容")

        return text_info

    return wrapper


class UIDesign(Action):
    """Class representing the UI Design action."""

    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)  # 需要调用LLM进一步丰富UI设计的prompt

    @parse
    def parse_requirement(self, context: str):
        """Parse UI Design draft from the context using regex."""
        pattern = r"## UI Design draft.*?\n(.*?)## Anything UNCLEAR"
        return context, pattern

    @parse
    def parse_ui_elements(self, context: str):
        """Parse Selected Elements from the context using regex."""
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
        """Draw icons using SDEngine."""
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
        save_dir = WORKSPACE_ROOT / "resources" / "codes"
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
        """Run the UI Design action."""
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


class UI(Role):
    """Class representing the UI Role."""

    def __init__(
        self,
        name="Catherine",
        profile="UI Design",
        goal="Finish a workable and good User Interface design based on a product design",
        constraints="Give clear layout description and use standard icons to finish the design",
        skills=["SD"],
    ):
        super().__init__(name, profile, goal, constraints)
        self.load_skills(skills)
        self._init_actions([UIDesign])
        self._watch([WritePRD])

    @load_engine
    def load_sd_engine(self):
        """Load the SDEngine."""
        file_name = ".tools.sd_engine"
        engine_name = "SDEngine"
        return file_name, engine_name

    def load_skills(self, skills):
        """Load skills for the UI Role."""
        # todo: 添加其他出图engine
        for skill in skills:
            if skill == "SD":
                self.sd_engine = self.load_sd_engine()
                logger.info(f"load skill engine {self.sd_engine}")
