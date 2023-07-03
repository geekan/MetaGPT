#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/1 22:50
@Author  : alexanderwu
@File    : test_azure_tts.py
"""
from metagpt.actions.azure_tts import AzureTTS


def test_azure_tts():
    azure_tts = AzureTTS("azure_tts")
    azure_tts.synthesize_speech(
        "zh-CN",
        "zh-CN-YunxiNeural",
        "Boy",
        "你好，我是卡卡",
        "output.wav")

    # 运行需要先配置 SUBSCRIPTION_KEY
    # TODO: 这里如果要检验，还要额外加上对应的asr，才能确保前后生成是接近一致的，但现在还没有
