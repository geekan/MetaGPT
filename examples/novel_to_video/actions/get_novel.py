# -*- coding: utf-8 -*-
# @Date    : 2024/2/5 16:28
# @Author  : 宏伟（散人）
# @Desc    :

from MetaGPT.metagpt.actions import Action


class Novel:
    id = 0
    title = ''
    alias = ''
    chapters = []

    def __init__(self, id, title, alias, chapters):
        self.id = id
        self.title = title
        self.alias = alias
        self.chapters = chapters


class Chapter:
    title = ''
    content = ''

    def __init__(self, title, content):
        self.title = title
        self.content = content

def GetNovelById(nid):
    # return Novel.query.get(nid)  #此处可以对接到数据库
    print('nid:', nid)
    chapter1 = Chapter(title='Chapter 1', content='This is the content of Chapter 1.')
    chapter2 = Chapter(title='Chapter 2', content='This is the content of Chapter 2.')
    novel = Novel(id=1, title='Novel 1', alias='N1', chapters=[chapter1, chapter2])
    return novel


class GetNovel(Action):
    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(**kwargs)

    async def run(self, novel_id: str = '', *args, **kwargs) -> Novel:
        novel = GetNovelById(novel_id)
        return novel




