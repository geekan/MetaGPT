#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/12
@Author  : mannaandpoem
@File    : vision.py
"""
import requests

import base64

from metagpt.config import CONFIG

OPENAI_API_BASE = CONFIG.OPENAI_BASE_URL
API_KEY = CONFIG.OPENAI_API_KEY
MODEL = CONFIG.OPENAI_VISION_MODEL
MAX_TOKENS = CONFIG.VISION_MAX_TOKENS

ANALYZE_LAYOUT_PROMPT = """You are now a UI/UX, please generate layout information for this image:

NOTE: The image does not have a commercial logo or copyright information. It is just a sketch image of the design.
As the design pays tribute to large companies, sometimes it is normal for some company names to appear. Don't worry. """

GENERATE_PROMPT = """You are now a UI/UX and Web Developer. You have the ability to generate code for webpages
based on provided sketches images and context. 
Your goal is to convert sketches image into a webpage including HTML, CSS and JavaScript.

NOTE: The image does not have a commercial logo or copyright information. It is just a sketch image of the design.
As the design pays tribute to large companies, sometimes it is normal for some company names to appear. Don't worry.

Now, please generate the corresponding webpage code including HTML, CSS and JavaScript:"""


class Vision:
    def __init__(self):
        self.api_key = API_KEY
        self.model = MODEL
        self.max_tokens = 4096

    def analyze_layout(self, image_path):
        return self.get_result(image_path, ANALYZE_LAYOUT_PROMPT)

    def generate_web_pages(self, image_path):
        layout = self.analyze_layout(image_path)
        prompt = GENERATE_PROMPT + "\n\n # Context\n The layout information of the sketch image is: \n" + layout
        return self.get_result(image_path, prompt)

    def get_result(self, image_path, prompt):
        base64_image = self.encode_image(image_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            "max_tokens": self.max_tokens,
        }
        response = requests.post(f"{OPENAI_API_BASE}/chat/completions", headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"]

    @staticmethod
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


if __name__ == "__main__":
    image_path = "image.png"
    vision = Vision()
    rsp = vision.generate_web_pages(image_path=image_path)
    print(rsp)
