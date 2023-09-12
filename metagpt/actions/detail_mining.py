#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/12 17:45
@Author  : fisherdeng
@File    : detail_mining.py
"""

from metagpt.actions import Action, ActionOutput
from metagpt.logs import logger

PROMPT_TEMPLATE = """
##讨论目标
{topic}

##讨论记录
{record}

##Format example
{format_example}
-----

任务: 参考 ##讨论目标 和 ##讨论记录 进一步询问你感兴趣的细节，字数不多于150字
特别注意1：你只是单纯地询问，不要赞同或否定任何人的任何观点
特别注意2:本次输出,仅包含 ##OUTPUT 这一主题，不要增加、减少或改变主题。输出时，以'##OUTPUT'开头，然后马上换行，再正式输出内容，仔细参考"##Format example"中的格式。
"""
FORMAT_EXAMPLE = """

##

##OUTPUT
...(请在这里输出你想询问的细节)

##

##
"""
OUTPUT_MAPPING = {
    "OUTPUT": (str, ...),
}


class DetailMining(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, topic, record) -> ActionOutput:

        prompt = PROMPT_TEMPLATE.format(topic,record,format_example=FORMAT_EXAMPLE)
        rsp = await self._aask_v1(prompt, "detail_mining", OUTPUT_MAPPING)
        return rsp
