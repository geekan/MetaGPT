# -*- coding: utf-8 -*-
# @Date    : 2024/2/5 16:28
# @Author  : 宏伟（散人）
# @Desc    :

import asyncio

import edge_tts

from MetaGPT.metagpt.actions import Action


class EdgeTTS(Action):
    voice: str = ''
    output: str = ''
    rate: str = ''  # 语速
    volume: str = ''  # 音量
    content: str = ''  # 需要转化的正文

    def __init__(self, voice: str = "zh-CN-YunxiNeural", output: str = '', rate: str = '+4%', volume: str = '+0%',
                 content: str = '',
                 *args, **kwargs):
        super().__init__(**kwargs)
        self.voice = voice
        self.output = output
        self.rate = rate
        self.volume = volume
        self.content = content

    async def run(self, *args, **kwargs) -> str:
        tts = edge_tts.Communicate(text=self.content, voice=self.voice, rate=self.rate, volume=self.volume)
        await tts.save(self.output)
        return self.output


async def main():
    content = """
   
另一个女孩小跑了过来，相比于前者，这个女孩并没有那么惊艳，但是依旧是一位不可多得美女。

她叫秦钰雯，经管学院大三年级，也是经管学院的院花。

眼前这位是她的闺蜜，名叫苏白粥，江城大学校学生会会长。

同时，也是江大唯一校花，以冰山美人著称的一位工作狂，计算机专业十年难遇的绝世美女。

“新生的事情比较多。”苏白粥平淡说道。

“说起来，昨天那件事情的后续是什么?小偷有没有被绳之以法？”

“一场误会。”

苏白粥面色不变。

警察已经把前因后果跟她解释了一遍。
    """
    action = EdgeTTS(output='../../workspace/tts/text2voice.mp3', content=content)
    result = await action.run()
    print('res:', result)


if __name__ == '__main__':
    asyncio.run(main())
