#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : action.py
"""
from abc import ABC
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_fixed

from metagpt.actions.action_output import ActionOutput
import metagpt.llm as LLM
from metagpt.utils.common import OutputParser
from metagpt.logs import logger
from metagpt.config import CONFIG

class Action(ABC):
    def __init__(self, name: str = '', context=None, llm: LLM = None):
        self.name: str = name
        if llm is None:
            llm=LLM.DEFAULT_LLM
        self.llm = llm
        self.context = context
        self.prefix = ""
        self.profile = ""
        self.desc = ""
        self.content = ""
        self.instruct_content = None

    def set_prefix(self, prefix, profile):
        """Set prefix for later usage"""
        self.prefix = prefix
        self.profile = profile

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        """Append default prefix"""
        if not system_msgs:
            system_msgs = []
        system_msgs.append(self.prefix)
        return await self.llm.aask(prompt, system_msgs)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def _aask_v1(self, prompt: str, output_class_name: str,
                       output_data_mapping: dict,
                       system_msgs: Optional[list[str]] = None) -> ActionOutput:
        """Append default prefix"""
        if not system_msgs:
            system_msgs = []
        system_msgs.append(self.prefix)
        if not CONFIG.no_api_mode:
            content = await self.llm.aask(prompt, system_msgs)
            logger.debug(content)
            output_class = ActionOutput.create_model_class(output_class_name, output_data_mapping)
            parsed_data = OutputParser.parse_data_with_mapping(content, output_data_mapping)
            logger.debug(parsed_data)
        try:
            instruct_content = output_class(**parsed_data)
            return ActionOutput(content, instruct_content)
        except Exception as e:
            print('Error:',e)
        print('自动运行出错，切换为手动运行')
        print('prompt为')
        print('\n'.join( system_msgs)+prompt)
        print('输入格式:')
        print(output_data_mapping)
        print('请准备输入,输入完成按ctrl+Z')
        while True:
            try:
                lines=[]
                while True:
                    try:
                        lines.append(input())
                    except:
                        break

                content ='\n'.join(lines)
                output_class = ActionOutput.create_model_class(output_class_name, output_data_mapping)
                parsed_data = OutputParser.parse_data_with_mapping(content, output_data_mapping)
                logger.debug(parsed_data)
                instruct_content = output_class(**parsed_data)
                return ActionOutput(content, instruct_content)
            except Exception as e:
                print('Error:',e)
                print('输入错误，请重试')


    async def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")
    