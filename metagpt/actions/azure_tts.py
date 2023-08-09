#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/9 22:22
@Author  : Leo Xiao
@File    : azure_tts.py
@Modified By: mashenquan, 2023-8-9, add more text formatting options
"""
from azure.cognitiveservices.speech import AudioConfig, SpeechConfig, SpeechSynthesizer

from metagpt.actions.action import Action
from metagpt.config import Config
from metagpt.const import WORKSPACE_ROOT


class AzureTTS(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.config = Config()

    # 参数参考：https://learn.microsoft.com/zh-cn/azure/cognitive-services/speech-service/language-support?tabs=tts#voice-styles-and-roles
    def synthesize_speech(self, lang, voice, text, output_file):
        subscription_key = self.config.get('AZURE_TTS_SUBSCRIPTION_KEY')
        region = self.config.get('AZURE_TTS_REGION')
        speech_config = SpeechConfig(
            subscription=subscription_key, region=region)

        speech_config.speech_synthesis_voice_name = voice
        audio_config = AudioConfig(filename=output_file)
        synthesizer = SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config)

        # More detail: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice
        ssml_string = f"""
            <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}' xmlns:mstts='http://www.w3.org/2001/mstts'>
                <voice name='{voice}'>
                    {text}
                </voice>
            </speak>
            """

        return synthesizer.speak_ssml_async(ssml_string).get()

    @staticmethod
    def role_style_text(role, style, text):
        return f'<mstts:express-as role="{role}" style="{style}">{text}</mstts:express-as>'

    @staticmethod
    def role_text(role, text):
        return f'<mstts:express-as role="{role}">{text}</mstts:express-as>'

    @staticmethod
    def style_text(style, text):
        return f'<mstts:express-as style="{style}">{text}</mstts:express-as>'

if __name__ == "__main__":
    azure_tts = AzureTTS("azure_tts")
    text = """
    女儿看见父亲走了进来，问道：
        <mstts:express-as role="YoungAdultFemale" style="calm">
            “您来的挺快的，怎么过来的？”
        </mstts:express-as>
        父亲放下手提包，说：
        <mstts:express-as role="OlderAdultMale" style="calm">
            “刚打车过来的，路上还挺顺畅。”
        </mstts:express-as>
    """
    path = WORKSPACE_ROOT / "tts"
    path.mkdir(exist_ok=True, parents=True)
    filename = path / "output.wav"
    azure_tts.synthesize_speech(
        "zh-CN",
        "zh-CN-YunxiNeural",
        text=AzureTTS.role_style_text(role="Boy", style="affectionate", text="你好，我是卡卡"),
        output_file=str(filename)
    )
