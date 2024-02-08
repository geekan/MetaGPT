#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/11 17:25
@Author  : alexanderwu
@File    : context_mixin.py
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from metagpt.config2 import Config
from metagpt.context import Context
from metagpt.provider.base_llm import BaseLLM


class ContextMixin(BaseModel):
    """Mixin class for context and config"""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    # Pydantic has bug on _private_attr when using inheritance, so we use private_* instead
    # - https://github.com/pydantic/pydantic/issues/7142
    # - https://github.com/pydantic/pydantic/issues/7083
    # - https://github.com/pydantic/pydantic/issues/7091

    # Env/Role/Action will use this context as private context, or use self.context as public context
    private_context: Optional[Context] = Field(default=None, exclude=True)
    # Env/Role/Action will use this config as private config, or use self.context.config as public config
    private_config: Optional[Config] = Field(default=None, exclude=True)

    # Env/Role/Action will use this llm as private llm, or use self.context._llm instance
    private_llm: Optional[BaseLLM] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def validate_context_mixin_extra(self):
        self._process_context_mixin_extra()
        return self

    def _process_context_mixin_extra(self):
        """Process the extra field"""
        kwargs = self.model_extra or {}
        self.set_context(kwargs.pop("context", None))
        self.set_config(kwargs.pop("config", None))
        self.set_llm(kwargs.pop("llm", None))

    def set(self, k, v, override=False):
        """Set attribute"""
        if override or not self.__dict__.get(k):
            self.__dict__[k] = v

    def set_context(self, context: Context, override=True):
        """Set context"""
        self.set("private_context", context, override)

    def set_config(self, config: Config, override=False):
        """Set config"""
        self.set("private_config", config, override)
        if config is not None:
            _ = self.llm  # init llm

    def set_llm(self, llm: BaseLLM, override=False):
        """Set llm"""
        self.set("private_llm", llm, override)

    @property
    def config(self) -> Config:
        """Role config: role config > context config"""
        if self.private_config:
            return self.private_config
        return self.context.config

    @config.setter
    def config(self, config: Config) -> None:
        """Set config"""
        self.set_config(config)

    @property
    def context(self) -> Context:
        """Role context: role context > context"""
        if self.private_context:
            return self.private_context
        return Context()

    @context.setter
    def context(self, context: Context) -> None:
        """Set context"""
        self.set_context(context)

    @property
    def llm(self) -> BaseLLM:
        """Role llm: if not existed, init from role.config"""
        # print(f"class:{self.__class__.__name__}({self.name}), llm: {self._llm}, llm_config: {self._llm_config}")
        if not self.private_llm:
            self.private_llm = self.context.llm_with_cost_manager_from_llm_config(self.config.llm)
        return self.private_llm

    @llm.setter
    def llm(self, llm: BaseLLM) -> None:
        """Set llm"""
        self.private_llm = llm
