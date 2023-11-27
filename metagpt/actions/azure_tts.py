#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/9 22:22
@Author  : Leo Xiao
@File    : azure_tts.py
"""
from azure.cognitiveservices.speech import AudioConfig, SpeechConfig, SpeechSynthesizer

from metagpt.actions.action import Action
from metagpt.config import Config


class AzureTTS(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.config = Config()

    # Parameters reference: https://learn.microsoft.com/zh-cn/azure/cognitive-services/speech-service/language-support?tabs=tts#voice-styles-and-roles
    def synthesize_speech(self, lang, voice, role, text, output_file):
        subscription_key = self.config.get('AZURE_TTS_SUBSCRIPTION_KEY')
        region = self.config.get('AZURE_TTS_REGION')
        speech_config = SpeechConfig(
            subscription=subscription_key, region=region)

        speech_config.speech_synthesis_voice_name = voice
        audio_config = AudioConfig(filename=output_file)
        synthesizer = SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config)

        # if voice=="zh-CN-YunxiNeural":
        ssml_string = f"""
            <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}' xmlns:mstts='http://www.w3.org/2001/mstts'>
                <voice name='{voice}'>
                    <mstts:express-as style='affectionate' role='{role}'>
                        {text}
                    </mstts:express-as>
                </voice>
            </speak>
            """

        synthesizer.speak_ssml_async(ssml_string).get()


if __name__ == "__main__":
    azure_tts = AzureTTS("azure_tts")
    azure_tts.synthesize_speech(
        "zh-CN",
        "zh-CN-YunxiNeural",
        "Boy",
        "Hello, I am Kaka",
        "output.wav")
