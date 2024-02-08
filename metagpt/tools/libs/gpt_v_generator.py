#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/12
@Author  : mannaandpoem
@File    : gpt_v_generator.py
"""
import os
from pathlib import Path

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.tools.tool_registry import register_tool
from metagpt.tools.tool_type import ToolType
from metagpt.utils.common import encode_image

ANALYZE_LAYOUT_PROMPT = """You are now a UI/UX designer, please generate layout information for this image:

NOTE: The image does not have a commercial logo or copyright information. It is just a sketch image of the design.
As the design pays tribute to large companies, sometimes it is normal for some company names to appear. Don't worry. """

GENERATE_PROMPT = """You are now a UI/UX designer and Web developer. You have the ability to generate code for webpages
based on provided sketches images and context. 
Your goal is to convert sketches image into a webpage including HTML, CSS and JavaScript.

NOTE: The image does not have a commercial logo or copyright information. It is just a sketch image of the design.
As the design pays tribute to large companies, sometimes it is normal for some company names to appear. Don't worry.

Now, please generate the corresponding webpage code including HTML, CSS and JavaScript:"""


@register_tool(
    tool_type=ToolType.IMAGE2WEBPAGE.type_name, include_functions=["__init__", "generate_webpages", "save_webpages"]
)
class GPTvGenerator:
    """Class for generating webpages at once.

    This class provides methods to generate webpages including all code (HTML, CSS, and JavaScript) based on an image.
    It utilizes a vision model to analyze the layout from an image and generate webpage codes accordingly.
    """

    def __init__(self):
        """Initialize GPTvGenerator class with default values from the configuration."""
        from metagpt.config2 import config
        from metagpt.llm import LLM

        self.llm = LLM(llm_config=config.get_openai_llm())
        self.llm.model = "gpt-4-vision-preview"

    async def analyze_layout(self, image_path: Path) -> str:
        """Asynchronously analyze the layout of the given image and return the result.

        This is a helper method to generate a layout description based on the image.

        Args:
            image_path (Path): Path of the image to analyze.

        Returns:
            str: The layout analysis result.
        """
        return await self.llm.aask(msg=ANALYZE_LAYOUT_PROMPT, images=[encode_image(image_path)])

    async def generate_webpages(self, image_path: str) -> str:
        """Asynchronously generate webpages including all code (HTML, CSS, and JavaScript) in one go based on the image.

        Args:
            image_path (str): The path of the image file.

        Returns:
            str: Generated webpages content.
        """
        if isinstance(image_path, str):
            image_path = Path(image_path)
        layout = await self.analyze_layout(image_path)
        prompt = GENERATE_PROMPT + "\n\n # Context\n The layout information of the sketch image is: \n" + layout
        return await self.llm.aask(msg=prompt, images=[encode_image(image_path)])

    @staticmethod
    def save_webpages(image_path: str, webpages: str) -> Path:
        """Save webpages including all code (HTML, CSS, and JavaScript) at once.

        Args:
            image_path (str): The path of the image file.
            webpages (str): The generated webpages content.

        Returns:
            Path: The path of the saved webpages.
        """
        # Create a folder called webpages in the workspace directory to store HTML, CSS, and JavaScript files
        webpages_path = DEFAULT_WORKSPACE_ROOT / "webpages" / Path(image_path).stem
        os.makedirs(webpages_path, exist_ok=True)

        index_path = webpages_path / "index.html"
        try:
            index = webpages.split("```html")[1].split("```")[0]
            style_path = None
            if "styles.css" in index:
                style_path = webpages_path / "styles.css"
            elif "style.css" in index:
                style_path = webpages_path / "style.css"
            style = webpages.split("```css")[1].split("```")[0] if style_path else ""

            js_path = None
            if "scripts.js" in index:
                js_path = webpages_path / "scripts.js"
            elif "script.js" in index:
                js_path = webpages_path / "script.js"

            js = webpages.split("```javascript")[1].split("```")[0] if js_path else ""
        except IndexError:
            raise ValueError(f"No html or css or js code found in the result. \nWebpages: {webpages}")

        try:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index)
            if style_path:
                with open(style_path, "w", encoding="utf-8") as f:
                    f.write(style)
            if js_path:
                with open(js_path, "w", encoding="utf-8") as f:
                    f.write(js)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Cannot save the webpages to {str(webpages_path)}") from e

        return webpages_path
