#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/11 14:43
# @Author  : alexanderwu
# @File    : action.py


from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from metagpt.actions.action_node import ActionNode
from metagpt.context_mixin import ContextMixin
from metagpt.schema import (
    CodePlanAndChangeContext,
    CodeSummarizeContext,
    CodingContext,
    RunCodeContext,
    SerializationMixin,
    TestingContext,
)
from metagpt.utils.project_repo import ProjectRepo


class Action(SerializationMixin, ContextMixin, BaseModel):
    """A class representing an action.

    Attributes:
        model_config: Configuration dictionary for the model.
        name: The name of the action.
        i_context: The input context for the action.
        prefix: The prefix for the action.
        desc: Description of the action.
        node: The action node.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = ""
    i_context: Union[
        dict, CodingContext, CodeSummarizeContext, TestingContext, RunCodeContext, CodePlanAndChangeContext, str, None
    ] = ""
    prefix: str = ""  # aask*时会加上prefix，作为system_message
    desc: str = ""  # for skill manager
    node: ActionNode = Field(default=None, exclude=True)

    @property
    def repo(self) -> ProjectRepo:
        """Get the project repository."""
        if not self.context.repo:
            self.context.repo = ProjectRepo(self.context.git_repo)
        return self.context.repo

    @property
    def prompt_schema(self):
        """Get the prompt schema."""
        return self.config.prompt_schema

    @property
    def project_name(self):
        """Get the project name."""
        return self.config.project_name

    @project_name.setter
    def project_name(self, value):
        """Set the project name."""
        self.config.project_name = value

    @property
    def project_path(self):
        """Get the project path."""
        return self.config.project_path

    @model_validator(mode="before")
    @classmethod
    def set_name_if_empty(cls, values):
        """Set the name if it's empty."""
        if "name" not in values or not values["name"]:
            values["name"] = cls.__name__
        return values

    @model_validator(mode="before")
    @classmethod
    def _init_with_instruction(cls, values):
        """Initialize with instruction."""
        if "instruction" in values:
            name = values["name"]
            i = values.pop("instruction")
            values["node"] = ActionNode(key=name, expected_type=str, instruction=i, example="", schema="raw")
        return values

    def set_prefix(self, prefix):
        """Set prefix for later usage"""
        self.prefix = prefix
        self.llm.system_prompt = prefix
        if self.node:
            self.node.llm = self.llm
        return self

    def __str__(self):
        """Return the class name as a string."""
        return self.__class__.__name__

    def __repr__(self):
        """Return the string representation of the class."""
        return self.__str__()

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        """Append default prefix"""
        return await self.llm.aask(prompt, system_msgs)

    async def _run_action_node(self, *args, **kwargs):
        """Run action node"""
        msgs = args[0]
        context = "## History Messages\n"
        context += "\n".join([f"{idx}: {i}" for idx, i in enumerate(reversed(msgs))])
        return await self.node.fill(context=context, llm=self.llm)

    async def run(self, *args, **kwargs):
        """Run action"""
        if self.node:
            return await self._run_action_node(*args, **kwargs)
        raise NotImplementedError("The run method should be implemented in a subclass.")
