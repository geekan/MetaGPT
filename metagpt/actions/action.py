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
from metagpt.callbacks import SenderInfo, BaseCallbackHandler, StdoutCallbackHander
from metagpt.actions.action_output import ActionOutput
from metagpt.llm import LLM
from metagpt.utils.common import OutputParser
from metagpt.logs import logger

class Action(ABC):
    def __init__(self, name: str = '', context=None, llm: LLM = None, sender_info: Optional[SenderInfo] = None):
        self.name: str = name
        if llm is None:
            llm = LLM()
        self.llm = llm
        self.context = context
        self.prefix = ""
        self.profile = ""
        self.desc = ""
        self.content = ""
        self.instruct_content = None
        self.sender_info = sender_info
        self.callback_handler: Optional[BaseCallbackHandler] = None

    def set_callback_handler(self, callback_handler: BaseCallbackHandler):
        self.callback_handler = callback_handler


    def set_prefix(self, prefix, profile):
        """Set prefix for later usage"""
        self.prefix = prefix
        self.profile = profile

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None,
                    callback_handler:Optional[BaseCallbackHandler]=None) -> str:
        """Append default prefix"""
        if callback_handler is None:
            if self.callback_handler is None:
                callback_handler = StdoutCallbackHander()
            else:
                callback_handler = self.callback_handler
        callback_handler.on_new_message(self.sender_info)
        if not system_msgs:
            system_msgs = []
        system_msgs.append(self.prefix)
        return await self.llm.aask(prompt, system_msgs, callback_handler)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def _aask_v1(self, prompt: str, output_class_name: str,
                       output_data_mapping: dict,
                       system_msgs: Optional[list[str]] = None,
                        callback_handler:Optional[BaseCallbackHandler]=None) -> ActionOutput:
        """Append default prefix"""
        if not system_msgs:
            system_msgs = []
        if callback_handler is None:
            if self.callback_handler is None:
                callback_handler = StdoutCallbackHander()
            else:
                callback_handler = self.callback_handler
        callback_handler.on_new_message(self.sender_info)
        system_msgs.append(self.prefix)
        content = await self.llm.aask(prompt, system_msgs, callback_handler)
        logger.debug(content)
        output_class = ActionOutput.create_model_class(output_class_name, output_data_mapping)
        parsed_data = OutputParser.parse_data_with_mapping(content, output_data_mapping)
        logger.debug(parsed_data)
        instruct_content = output_class(**parsed_data)
        return ActionOutput(content, instruct_content)

    async def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")
    