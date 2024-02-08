#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : text_to_speech.py
@Desc    : Text-to-Speech skill, which provides text-to-speech functionality
"""
import metagpt.config2
from metagpt.config2 import Config
from metagpt.const import BASE64_FORMAT
from metagpt.tools.azure_tts import oas3_azsure_tts
from metagpt.tools.iflytek_tts import oas3_iflytek_tts
from metagpt.utils.s3 import S3


async def text_to_speech(
    text,
    lang="zh-CN",
    voice="zh-CN-XiaomoNeural",
    style="affectionate",
    role="Girl",
    config: Config = metagpt.config2.config,
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
    :param iflytek_app_id: Application ID is used to access your iFlyTek service API, see: `https://console.xfyun.cn/services/tts`
    :param iflytek_api_key: WebAPI argument, see: `https://console.xfyun.cn/services/tts`
    :param iflytek_api_secret: WebAPI argument, see: `https://console.xfyun.cn/services/tts`
    :return: Returns the Base64-encoded .wav/.mp3 file data if successful, otherwise an empty string.

    """

    subscription_key = config.azure_tts_subscription_key
    region = config.azure_tts_region
    if subscription_key and region:
        audio_declaration = "data:audio/wav;base64,"
        base64_data = await oas3_azsure_tts(text, lang, voice, style, role, subscription_key, region)
        s3 = S3(config.s3)
        url = await s3.cache(data=base64_data, file_ext=".wav", format=BASE64_FORMAT)
        if url:
            return f"[{text}]({url})"
        return audio_declaration + base64_data if base64_data else base64_data

    iflytek_app_id = config.iflytek_app_id
    iflytek_api_key = config.iflytek_api_key
    iflytek_api_secret = config.iflytek_api_secret
    if iflytek_app_id and iflytek_api_key and iflytek_api_secret:
        audio_declaration = "data:audio/mp3;base64,"
        base64_data = await oas3_iflytek_tts(
            text=text, app_id=iflytek_app_id, api_key=iflytek_api_key, api_secret=iflytek_api_secret
        )
        s3 = S3(config.s3)
        url = await s3.cache(data=base64_data, file_ext=".mp3", format=BASE64_FORMAT)
        if url:
            return f"[{text}]({url})"
        return audio_declaration + base64_data if base64_data else base64_data

    raise ValueError(
        "azure_tts_subscription_key, azure_tts_region, iflytek_app_id, iflytek_api_key, iflytek_api_secret error"
    )
