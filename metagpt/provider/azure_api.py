#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:55
@Author  : alexanderwu
@File    : azure_api.py
"""

import json

import requests
from metagpt.logs import logger

import openai
from metagpt.provider.openai_api import OpenAIGPTAPI
from metagpt.config import Config


class AzureGPTAPI(OpenAIGPTAPI):
    """Access GPT capabilities through the Azure interface, which requires separate application
    # FIXME: Here we use engine (deployment_name), whereas we used to use model
    - Model deployment: https://oai.azure.com/portal/deployment
    - Python code example: https://learn.microsoft.com/zh-cn/azure/cognitive-services/openai/chatgpt-quickstart?pivots=programming-language-python&tabs=command-line
    - endpoint  https://deepwisdom-openai.openai.azure.com/
    """
    def __init__(self):
        super().__init__()
        config = self.config
        self.api_key = config.get("AZURE_OPENAI_KEY")
        self.base_url = config.get("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = config.get("AZURE_DEPLOYMENT_NAME")
        self.api_version = config.get("AZURE_OPENAI_API_VERSION")
        self.api_type = "azure"
        # openai.api_key = self.api_key = config.get("AZURE_OPENAI_KEY")
        # openai.api_base = self.base_url = config.get("AZURE_OPENAI_ENDPOINT")
        # self.deployment_name = config.get("AZURE_DEPLOYMENT_NAME")
        # openai.api_version = self.api_version = config.get("AZURE_OPENAI_API_VERSION")
        # openai.api_type = self.api_type = "azure"

    def completion(self, messages: list[dict]):
        """
        :param messages: 历史对话，标明了每个角色说了什么
        :return: 返回例子如下
        {
            "id": "ID of your call",
            "object": "text_completion",
            "created": 1675444965,
            "model": "text-davinci-002",
            "choices": [
                {
                    "text": " there lived in a little village a woman who was known as the meanest",
                    "index": 0,
                    "finish_reason": "length",
                    "logprobs": null
                }
            ],
            "usage": {
                "completion_tokens": 16,
                "prompt_tokens": 3,
                "total_tokens": 19
            }
        }
        """
        url = self.base_url + "/openai/deployments/" + self.deployment_name + "/chat/completions?api-version=" + self.api_version
        payload = {"messages": messages}

        rsp = requests.post(url, headers={"api-key": self.api_key, "Content-Type": "application/json"}, json=payload,
                            timeout=60)

        response = json.loads(rsp.text)
        formatted_response = json.dumps(response, indent=4)
        # logger.info(formatted_response)
        return response

    def get_choice_text(self, rsp):
        """要求提供choice第一条文本"""
        return rsp.get("choices")[0]["message"]['content']
