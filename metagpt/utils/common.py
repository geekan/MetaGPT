#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 16:07
@Author  : alexanderwu
@File    : common.py
"""
import os
import re
import ast
import subprocess
import inspect
from pathlib import Path

from metagpt.const import PROJECT_ROOT, TMP
from metagpt.logs import logger


def check_cmd_exists(command) -> int:
    """ 检查命令是否存在
    :param command: 待检查的命令
    :return: 如果命令存在，返回0，如果不存在，返回非0
    """
    check_command = 'command -v ' + command + ' >/dev/null 2>&1 || { echo >&2 "no mermaid"; exit 1; }'
    result = os.system(check_command)
    return result


class CodeParser:

    @classmethod
    def parse_block(cls, block: str, text: str) -> str:
        blocks = cls.parse_blocks(text)
        for k, v in blocks.items():
            if block in k:
                return v
        return ""

    @classmethod
    def parse_blocks(cls, text: str):
        # 首先根据"##"将文本分割成不同的block
        blocks = text.split("##")

        # 创建一个字典，用于存储每个block的标题和内容
        block_dict = {}

        # 遍历所有的block
        for block in blocks:
            # 如果block不为空，则继续处理
            if block.strip() != "":
                # 将block的标题和内容分开，并分别去掉前后的空白字符
                block_title, block_content = block.split("\n", 1)
                block_dict[block_title.strip()] = block_content.strip()

        return block_dict

    @classmethod
    def parse_code(cls, block: str, text: str, lang: str="") -> str:
        if block:
            text = cls.parse_block(block, text)
        pattern = rf'```{lang}.*?\s+(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            code = match.group(1)
        else:
            logger.error(f"{pattern} not match following text:")
            logger.error(text)
            raise Exception
        return code

    @classmethod
    def parse_str(cls, block: str, text: str, lang: str=""):
        code = cls.parse_code(block, text, lang)
        code = code.split("=")[-1]
        code = code.strip().strip("'").strip("\"")
        return code

    @classmethod
    def parse_file_list(cls, block: str, text: str, lang: str="") -> list[str]:
        # Regular expression pattern to find the tasks list.
        code = cls.parse_code(block, text, lang)
        pattern = r'\s*(.*=.*)?(\[.*\])'

        # Extract tasks list string using regex.
        match = re.search(pattern, code, re.DOTALL)
        if match:
            tasks_list_str = match.group(2)

            # Convert string representation of list to a Python list using ast.literal_eval.
            tasks = ast.literal_eval(tasks_list_str)
        else:
            raise Exception
        return tasks


class NoMoneyException(Exception):
    """Raised when the operation cannot be completed due to insufficient funds"""
    def __init__(self, amount, message="Insufficient funds"):
        self.amount = amount
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} -> Amount required: {self.amount}'


def print_members(module, indent=0):
    """
    https://stackoverflow.com/questions/1796180/how-can-i-get-a-list-of-all-classes-within-current-module-in-python
    :param module:
    :param indent:
    :return:
    """
    prefix = ' ' * indent
    for name, obj in inspect.getmembers(module):
        print(name, obj)
        if inspect.isclass(obj):
            print(f'{prefix}Class: {name}')
            # print the methods within the class
            if name in ['__class__', '__base__']:
                continue
            print_members(obj, indent + 2)
        elif inspect.isfunction(obj):
            print(f'{prefix}Function: {name}')
        elif inspect.ismethod(obj):
            print(f'{prefix}Method: {name}')
