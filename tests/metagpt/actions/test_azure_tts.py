#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/1 22:50
@Author  : alexanderwu
@File    : test_azure_tts.py
@Modified By: mashenquan, 2023-8-9, add more text formatting options
"""
from metagpt.actions.azure_tts import AzureTTS
from metagpt.const import WORKSPACE_ROOT


def test_azure_tts():
    azure_tts = AzureTTS("azure_tts")
    text = """
        女儿看见父亲走了进来，问道：
            <mstts:express-as role="YoungAdultFemale" style="calm">
                “您来的挺快的，怎么过来的？”
            </mstts:express-as>
            父亲放下手提包，说：
            <mstts:express-as role="OlderAdultMale" style="calm">
                “Writing a binary file in Python is similar to writing a regular text file, but you'll work with bytes instead of strings.”
            </mstts:express-as>
        """
    path = WORKSPACE_ROOT / "tts"
    path.mkdir(exist_ok=True, parents=True)
    filename = path / "girl.wav"
    result = azure_tts.synthesize_speech(
        "zh-CN",
        "zh-CN-XiaomoNeural",
        text=text,
        output_file=str(filename))

    print(result)

    # 运行需要先配置 SUBSCRIPTION_KEY
    # TODO: 这里如果要检验，还要额外加上对应的asr，才能确保前后生成是接近一致的，但现在还没有


if __name__ == '__main__':
    test_azure_tts()
