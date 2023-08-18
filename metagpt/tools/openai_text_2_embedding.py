#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : openai_text_2_vector.py
@Desc    : OpenAI Text-to-Vector OAS3 api, which provides text-to-vector functionality.
"""
import os

class OpenAIText2Vector:
    def __init__(self, openai_api_key):
        """
        :param openai_api_key: OpenAI API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
        """
        self.openai_api_key = openai_api_key if openai_api_key else os.environ.get('OPENAI_API_KEY')

    def text_2_vector(self, text, size_type="1024x1024"):
        """Text to image

        :param text: The text used for image conversion.
        :param size_type: One of ['256x256', '512x512', '1024x1024']
        :return: The image data is returned in Base64 encoding.
        """

        class ImageUrl(BaseModel):
            url: str

        class ImageResult(BaseModel):
            data: List[ImageUrl]
            created: int

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        data = {"prompt": text, "n": 1, "size": size_type}
        try:
            response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx responses
            result = ImageResult(**response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred:{e}")
            return ""
        if len(result.data) > 0:
            return OpenAIText2Image.get_image_data(result.data[0].url)
        return ""