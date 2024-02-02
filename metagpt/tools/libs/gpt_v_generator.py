#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/12
@Author  : mannaandpoem
@File    : gpt_v_generator.py
"""
import base64
import os
from pathlib import Path

import requests

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.tools.tool_registry import register_tool
from metagpt.tools.tool_types import ToolTypes

ANALYZE_LAYOUT_PROMPT = """You are now a UI/UX, please generate layout information for this image:

NOTE: The image does not have a commercial logo or copyright information. It is just a sketch image of the design.
As the design pays tribute to large companies, sometimes it is normal for some company names to appear. Don't worry. """

GENERATE_PROMPT = """You are now a UI/UX and Web Developer. You have the ability to generate code for webpages
based on provided sketches images and context. 
Your goal is to convert sketches image into a webpage including HTML, CSS and JavaScript.

NOTE: The image does not have a commercial logo or copyright information. It is just a sketch image of the design.
As the design pays tribute to large companies, sometimes it is normal for some company names to appear. Don't worry.

Now, please generate the corresponding webpage code including HTML, CSS and JavaScript:"""


@register_tool(
    tool_type=ToolTypes.IMAGE2WEBPAGE.type_name, include_functions=["__init__", "generate_webpages", "save_webpages"]
)
class GPTvGenerator:
    """Class for generating webpages at once.

    This class provides methods to generate webpages including all code (HTML, CSS, and JavaScript) based on an image.
    It utilizes a vision model to analyze the layout from an image and generate webpage codes accordingly.
    """

    def __init__(self):
        """Initialize GPTvGenerator class with default values from the configuration."""
        from metagpt.config2 import config

        self.api_key = config.llm.api_key
        self.api_base = config.llm.base_url
        self.model = config.openai_vision_model
        self.max_tokens = config.vision_max_tokens

    def analyze_layout(self, image_path):
        """Analyze the layout of the given image and return the result.

        This is a helper method to generate a layout description based on the image.

        Args:
            image_path (str): Path of the image to analyze.

        Returns:
            str: The layout analysis result.
        """
        return self.get_result(image_path, ANALYZE_LAYOUT_PROMPT)

    def generate_webpages(self, image_path):
        """Generate webpages including all code (HTML, CSS, and JavaScript) in one go based on the image.

        Args:
            image_path (str): The path of the image file.

        Returns:
            str: Generated webpages content.
        """
        layout = self.analyze_layout(image_path)
        prompt = GENERATE_PROMPT + "\n\n # Context\n The layout information of the sketch image is: \n" + layout
        result = self.get_result(image_path, prompt)
        return result

    def get_result(self, image_path, prompt):
        """Get the result from the vision model based on the given image path and prompt.

        Args:
            image_path (str): Path of the image to analyze.
            prompt (str): Prompt to use for the analysis.

        Returns:
            str: The model's response as a string.
        """
        base64_image = self.encode_image(image_path)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            "max_tokens": self.max_tokens,
        }
        response = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)

        if response.status_code != 200:
            raise ValueError(f"Request failed with status {response.status_code}, {response.text}")
        else:
            return response.json()["choices"][0]["message"]["content"]

    @staticmethod
    def encode_image(image_path):
        """Encode the image at the given path to a base64 string.

        Args:
            image_path (str): Path of the image to encode.

        Returns:
            str: The base64 encoded string of the image.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @staticmethod
    def save_webpages(image_path, webpages) -> Path:
        """Save webpages including all code (HTML, CSS, and JavaScript) at once.

        Args:
            image_path (str): The path of the image file.
            webpages (str): The generated webpages content.

        Returns:
            Path: The path of the saved webpages.
        """
        # 在workspace目录下，创建一个名为下webpages的文件夹，用于存储html、css和js文件
        webpages_path = DEFAULT_WORKSPACE_ROOT / "webpages" / Path(image_path).stem
        os.makedirs(webpages_path, exist_ok=True)

        index_path = webpages_path / "index.html"

        try:
            index = webpages.split("```html")[1].split("```")[0]
        except IndexError:
            index = "No html code found in the result, please check your image and try again." + "\n" + webpages

        try:
            if "styles.css" in index:
                style_path = webpages_path / "styles.css"
            elif "style.css" in index:
                style_path = webpages_path / "style.css"
            else:
                style_path = None
            style = webpages.split("```css")[1].split("```")[0] if style_path else ""

            if "scripts.js" in index:
                js_path = webpages_path / "scripts.js"
            elif "script.js" in index:
                js_path = webpages_path / "script.js"
            else:
                js_path = None
            js = webpages.split("```javascript")[1].split("```")[0] if js_path else ""
        except IndexError:
            raise ValueError("No css or js code found in the result, please check your image and try again.")

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
