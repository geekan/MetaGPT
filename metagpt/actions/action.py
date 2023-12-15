#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : action.py
@Modified By: mashenquan, 2023/8/20. Add function return annotations.
@Modified By: mashenquan, 2023/9/8. Replace LLM with LLMFactory
"""

from __future__ import annotations

from abc import ABC
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions.action_output import ActionOutput
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.provider.postprecess.llm_output_postprecess import llm_output_postprecess
from metagpt.utils.common import OutputParser
from metagpt.utils.utils import general_after_log


class Action(ABC):
    def __init__(self, name: str = "", context=None, llm: BaseGPTAPI = None):
        self.name: str = name
        if llm is None:
            llm = LLM()
        self.llm = llm
        self.context = context
        self.prefix = ""  # aask*时会加上prefix，作为system_message
        self.profile = ""  # FIXME: USELESS
        self.desc = ""  # for skill manager
        self.nodes = ...

        # Output, useless
        # self.content = ""
        # self.instruct_content = None
        # self.env = None

    # def set_env(self, env):
    #     self.env = env

    def set_prefix(self, prefix, profile):
        """Set prefix for later usage"""
        self.prefix = prefix
        self.profile = profile
        return self

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

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _aask_v1(
        self,
        prompt: str,
        output_class_name: str,
        output_data_mapping: dict,
        system_msgs: Optional[list[str]] = None,
        format="markdown",  # compatible to original format
    ) -> ActionOutput:
        content = await self.llm.aask(prompt, system_msgs)
        logger.debug(f"llm raw output:\n{content}")
        output_class = ActionOutput.create_model_class(output_class_name, output_data_mapping)

        if format == "json":
            parsed_data = llm_output_postprecess(output=content, schema=output_class.schema(), req_key="[/CONTENT]")

        else:  # using markdown parser
            parsed_data = OutputParser.parse_data_with_mapping(content, output_data_mapping)

        logger.debug(f"parsed_data:\n{parsed_data}")
        instruct_content = output_class(**parsed_data)
        return ActionOutput(content, instruct_content)

    async def run(self, *args, **kwargs) -> str | ActionOutput | None:
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")
