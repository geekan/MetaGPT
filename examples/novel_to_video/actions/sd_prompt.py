# -*- coding: utf-8 -*-
# @Date    : 2024/2/5 16:28
# @Author  : 宏伟（散人）
# @Desc    :

import asyncio
from MetaGPT.metagpt.actions import Action
from MetaGPT.examples.novel_to_video.utils.textTools import replace_newlines


class MakeSDPrompt(Action):
    content: str = ""

    def __init__(self, name: str = "", content: str = "", *args, **kwargs):
        super().__init__(**kwargs)
        self.content = content

    async def run(self, *args, **kwargs) -> str:
        REWRITE_PROMPT = """
        Please extract the keywords from this article and supplement them with visual descriptions, and divide them into English words.
        1.If there are characters, use 1girl or 1boy or Ngirls or Nboys to start.(N is the number of characters)
        2.You need to describe the details in the picture as much as possible, including expression, actions, clothing, posture, background, environment,etc
        3.The output must be strictly in the specified language, English.
        4.Words must be separated by a comma.
        5.The content you output can only contain words that describe the image
        The text delimited by triple backticks.
        ```{content}```
        """
        prompt = REWRITE_PROMPT.format(content=self.content)
        resp = await self._aask(prompt=prompt)
        resp = replace_newlines(resp)  # 去除换行
        return resp


async def main():
    content = """
    这是我第一次来到派出所，被误会了。
    """
    action = MakeSDPrompt(content=content)
    result = await action.run()
    print('res:', result)


if __name__ == '__main__':
    asyncio.run(main())
