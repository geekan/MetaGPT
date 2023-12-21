#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/08/04 10:00
@Author  : ishaan-jaff
@File    : openai.py
"""
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.provider.openai_api import CostManager, RateLimiter
from metagpt.config import CONFIG

class liteLLM(BaseGPTAPI, RateLimiter):
    def __init__(self):
        self.__init_openai(CONFIG)
        self.model = CONFIG.model # litellm model
        self._cost_manager = CostManager()
        RateLimiter.__init__(self, rpm=self.rpm)

    def _chat_completion(self, messages: list[dict], model: str) -> dict:
        rsp = self.llm.ChatCompletion.create(**self._cons_kwargs(messages))
        self._update_costs(rsp)
        return rsp

"""
https://github.com/BerriAI/litellm/

usage for litellm
from litellm import completion

## set ENV variables
# ENV variables can be set in .env file, too. Example in .env.example
os.environ["OPENAI_API_KEY"] = "openai key"
os.environ["COHERE_API_KEY"] = "cohere key"

messages = [{ "content": "Hello, how are you?","role": "user"}]

model_name = "replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"

# llama2 call
response = completion(model_name, messages)

# openai call
response = completion(model="gpt-3.5-turbo", messages=messages)

# cohere call
response = completion("command-nightly", messages)

# azure openai call
response = completion("chatgpt-test", messages, azure=True)

# openrouter call
response = completion("google/palm-2-codechat-bison", messages)


"""