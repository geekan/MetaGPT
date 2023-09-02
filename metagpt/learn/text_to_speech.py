#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : text_to_speech.py
@Desc    : Text-to-Speech skill, which provides text-to-speech functionality
"""
import openai

from metagpt.config import CONFIG
from metagpt.const import BASE64_FORMAT
from metagpt.tools.azure_tts import oas3_azsure_tts
from metagpt.utils.s3 import S3


async def text_to_speech(
    text,
    lang="zh-CN",
    voice="zh-CN-XiaomoNeural",
    style="affectionate",
    role="Girl",
    subscription_key="",
    region="",
    **kwargs,
):
    """Text to speech
    For more details, check out:`https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts`

    :param lang: The value can contain a language code such as en (English), or a locale such as en-US (English - United States). For more details, checkout: `https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts`
    :param voice: For more details, checkout: `https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts`, `https://speech.microsoft.com/portal/voicegallery`
    :param style: Speaking style to express different emotions like cheerfulness, empathy, and calm. For more details, checkout: `https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts`
    :param role: With roles, the same voice can act as a different age and gender. For more details, checkout: `https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts`
    :param text: The text used for voice conversion.
    :param subscription_key: key is used to access your Azure AI service API, see: `https://portal.azure.com/` > `Resource Management` > `Keys and Endpoint`
    :param region: This is the location (or region) of your resource. You may need to use this field when making calls to this API.
    :return: Returns the Base64-encoded .wav file data if successful, otherwise an empty string.

    """
    audio_declaration = "data:audio/wav;base64,"
    if (CONFIG.AZURE_TTS_SUBSCRIPTION_KEY and CONFIG.AZURE_TTS_REGION) or (subscription_key and region):
        base64_data = await oas3_azsure_tts(text, lang, voice, style, role, subscription_key, region)
        s3 = S3()
        url = await s3.cache(data=base64_data, file_ext=".wav", format=BASE64_FORMAT)
        if url:
            return f"[{text}]({url})"
        return audio_declaration + base64_data if base64_data else base64_data

    raise openai.error.InvalidRequestError("缺少必要的参数")
