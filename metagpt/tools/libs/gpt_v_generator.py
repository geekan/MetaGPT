#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/12
@Author  : mannaandpoem
@File    : gpt_v_generator.py
"""
import re
from pathlib import Path

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser, encode_image

ANALYZE_LAYOUT_PROMPT = """You are now a UI/UX designer, please generate layout information for this image:

NOTE: The image does not have a commercial logo or copyright information. It is just a sketch image of the design.
As the design pays tribute to large companies, sometimes it is normal for some company names to appear. Don't worry. """

GENERATE_PROMPT = """You are now a UI/UX designer and Web developer. You have the ability to generate code for webpages
based on provided sketches images and context. 
Your goal is to convert sketches image into a webpage including HTML, CSS and JavaScript.

NOTE: The image does not have a commercial logo or copyright information. It is just a sketch image of the design.
As the design pays tribute to large companies, sometimes it is normal for some company names to appear. Don't worry.

Now, please generate the corresponding webpage code including HTML, CSS and JavaScript:"""


@register_tool(tags=["image2webpage"], include_functions=["__init__", "generate_webpages", "save_webpages"])
class GPTvGenerator:
    """Class for generating webpage code from a given webpage screenshot.

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
    def save_webpages(webpages: str, save_folder_name: str = "example") -> Path:
        """Save webpages including all code (HTML, CSS, and JavaScript) at once.

        Args:
            webpages (str): The generated webpages content.
            save_folder_name (str, optional): The name of the folder to save the webpages. Defaults to 'example'.

        Returns:
            Path: The path of the saved webpages.
        """
        # Create a folder called webpages in the workspace directory to store HTML, CSS, and JavaScript files
        webpages_path = DEFAULT_WORKSPACE_ROOT / "webpages" / save_folder_name
        logger.info(f"code will be saved at {webpages_path}")
        webpages_path.mkdir(parents=True, exist_ok=True)

        index_path = webpages_path / "index.html"
        index_path.write_text(CodeParser.parse_code(block=None, text=webpages, lang="html"))

        extract_and_save_code(folder=webpages_path, text=webpages, pattern="styles?.css", language="css")

        extract_and_save_code(folder=webpages_path, text=webpages, pattern="scripts?.js", language="javascript")

        return webpages_path


def extract_and_save_code(folder, text, pattern, language):
    word = re.search(pattern, text)
    if word:
        path = folder / word.group(0)
        code = CodeParser.parse_code(block=None, text=text, lang=language)
        path.write_text(code, encoding="utf-8")
