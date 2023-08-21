#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/7
@Author  : mashenquan
@File    : meta_action.py
@Desc   : I am attempting to incorporate certain symbol concepts from UML into MetaGPT, enabling it to have the
            ability to freely construct flows through symbol concatenation. Simultaneously, I am also striving to
            make these symbols configurable and standardized, making the process of building flows more convenient.
            For more about `fork` node in activity diagrams, see: `https://www.uml-diagrams.org/activity-diagrams.html`
          This file defines a meta action capable of generating arbitrary actions at runtime based on a
            configuration file.
"""

from typing import Type

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.roles.uml_meta_role_options import MetaActionOptions
from metagpt.schema import Message


class MetaAction(Action):
    def __init__(self, options, action_options: MetaActionOptions, llm=None, **kwargs):
        super(MetaAction, self).__init__(options=options,
                                         name=action_options.name,
                                         context=kwargs.get("context"),
                                         llm=llm)
        self.prompt = action_options.format_prompt(**kwargs)
        self.action_options = action_options
        self.kwargs = kwargs

    def __str__(self):
        """Return `topic` value when str()"""
        return self.action_options.topic

    def __repr__(self):
        """Show `topic` value when debug"""
        return self.action_options.topic

    async def run(self, messages, *args, **kwargs):
        if len(messages) < 1 or not isinstance(messages[0], Message):
            raise ValueError("Invalid args, a tuple of List[Message] is expected")

        logger.debug(self.prompt)
        rsp = await self._aask(prompt=self.prompt)
        logger.debug(rsp)
        self._set_result(rsp)
        return self.rsp

    def _set_result(self, rsp):
        if self.action_options.rsp_begin_tag and self.action_options.rsp_begin_tag in rsp:
            ix = rsp.index(self.action_options.rsp_begin_tag)
            rsp = rsp[ix + len(self.action_options.rsp_begin_tag):]
        if self.action_options.rsp_end_tag and self.action_options.rsp_end_tag in rsp:
            ix = rsp.index(self.action_options.rsp_end_tag)
            rsp = rsp[0:ix]
        self.rsp = rsp.strip()

    @staticmethod
    def get_action_type(topic: str):
        """Create a runtime :class:`Action` subclass"""
        action_type: Type["Action"] = type(topic, (Action,), {"name": topic})
        return action_type
