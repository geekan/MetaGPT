# -*- coding: utf-8 -*-
# @Date    : 2024/2/5 16:28
# @Author  : 宏伟（散人）
# @Desc    :
import asyncio
from MetaGPT.metagpt.actions import Action
from metagpt.utils.common import OutputParser


# 内容分段
class Segment(Action):
    content: str = ""

    def __init__(self, name: str = "", content: str = "", *args, **kwargs):
        super().__init__(**kwargs)
        self.content = content

    async def run(self, *args, **kwargs) -> list:
        REWRITE_PROMPT = """
        Your task will segment the following text.The text delimited by triple backticks.
        1.Each paragraph has less than 20 words.
        2.Ignoring words unrelated to the plot of the story.
        3.You output must in the array format like ["xxx", "xxx", "xxx",...,"xxx"].
        4.Do not have extra spaces or line breaks.
        ```{content}```
        """

        prompt = REWRITE_PROMPT.format(content=self.content)
        print('prompt:', prompt)
        resp = await self._aask(prompt=prompt)
        return OutputParser.extract_struct(resp, list)


async def main():
    content = """
    这是我第一次来到派出所，被误会了。警察带我去审讯室，询问个人信息。我无辜地回答问题，警察怀疑我私闯民宅。我解释说那是我家，警察查资料后才明白误会。原来房子被我哥租出去了。警长亲自来解释误会，原来我是烈士之子。我拒绝留宿邀请，离开派出所。第二天，我报名后发现无处可住，郁闷之际，遇见学姐帮我进图书馆。她帮我刷脸进入，让我感慨不已。
    """
    action = Segment(content=content)
    result = await action.run()
    print('res:', result)


if __name__ == '__main__':
    asyncio.run(main())
