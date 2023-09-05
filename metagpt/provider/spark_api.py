#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/21 11:15
@Author  : Leo Xiao
@File    : anthropic_api.py
"""

from typing import Optional
from metagpt.provider import SparkApi

from metagpt.config import CONFIG

def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    while (getlength(text) > 8000):
        del text[0]
    return text

class Spark:
    system_prompt = 'You are a helpful assistant.'

    def _user_msg(self, msg: str) -> dict[str, str]:
        return {"role": "user", "content": msg}

    def _assistant_msg(self, msg: str) -> dict[str, str]:
        return {"role": "assistant", "content": msg}

    def _system_msg(self, msg: str) -> dict[str, str]:
        return {"role": "system", "content": msg}

    def _system_msgs(self, msgs: list[str]) -> list[dict[str, str]]:
        return [self._system_msg(msg) for msg in msgs]

    def _default_system_msg(self):
        return self._system_msg(self.system_prompt)
    def ask(self, msg: str):
        message = [self._user_msg(msg)]
        SparkApi.main(CONFIG.xinghuo_appid,CONFIG.xinghuo_api_key,CONFIG.xinghuo_api_secret,"ws://spark-api.xf-yun.com/v2.1/chat","generalv2",message)
        rsp = SparkApi.answer
        return rsp

    async def aask(self, msg: str, system_msgs: Optional[list[str]] = None) -> str:
        if system_msgs:
            message = self._system_msgs(system_msgs) + [self._user_msg(msg)]
        else:
            message = [self._user_msg(msg)]
        SparkApi.main(CONFIG.xinghuo_appid,CONFIG.xinghuo_api_key,CONFIG.xinghuo_api_secret,"ws://spark-api.xf-yun.com/v2.1/chat","generalv2",message)
        rsp = SparkApi.answer
        return rsp
