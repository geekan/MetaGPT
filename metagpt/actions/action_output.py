#!/usr/bin/env python
# coding: utf-8
# @Time    : 2023/7/11 10:03
# @Author  : chengmaoyu
# @File    : action_output


from pydantic import BaseModel


class ActionOutput:
    """A class to represent the output of an action.

    Attributes:
        content: A string representing the content of the output.
        instruct_content: An instance of BaseModel representing structured content.

    Args:
        content: A string representing the content of the output.
        instruct_content: An instance of BaseModel representing structured content.
    """

    content: str
    instruct_content: BaseModel

    def __init__(self, content: str, instruct_content: BaseModel):
        self.content = content
        self.instruct_content = instruct_content
