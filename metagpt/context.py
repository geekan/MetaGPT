#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 16:32
@Author  : alexanderwu
@File    : context.py
"""
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict

from metagpt.config2 import Config
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import OPTIONS
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.git_repository import GitRepository


class AttrDict(BaseModel):
    """A dict-like object that allows access to keys as attributes, compatible with Pydantic."""

    model_config = ConfigDict(extra="allow")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__dict__.update(kwargs)

    def __getattr__(self, key):
        return self.__dict__.get(key, None)

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def __delattr__(self, key):
        if key in self.__dict__:
            del self.__dict__[key]
        else:
            raise AttributeError(f"No such attribute: {key}")


class LLMMixin:
    """Mixin class for LLM"""

    # _config: Optional[Config] = None
    _llm_config: Optional[LLMConfig] = None
    _llm_instance: Optional[BaseLLM] = None

    def use_llm(self, name: Optional[str] = None, provider: LLMType = LLMType.OPENAI):
        """Use a LLM provider"""
        # 更新LLM配置
        self._llm_config = self._config.get_llm_config(name, provider)
        # 重置LLM实例
        self._llm_instance = None

    @property
    def llm(self) -> BaseLLM:
        """Return the LLM instance"""
        if not self._llm_config:
            self.use_llm()
        if not self._llm_instance and self._llm_config:
            self._llm_instance = create_llm_instance(self._llm_config)
        return self._llm_instance


class Context(LLMMixin, BaseModel):
    """Env context for MetaGPT"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    kwargs: AttrDict = AttrDict()
    config: Config = Config.default()
    git_repo: Optional[GitRepository] = None
    src_workspace: Optional[Path] = None
    cost_manager: CostManager = CostManager()

    @property
    def file_repo(self):
        return self.git_repo.new_file_repository()

    @property
    def options(self):
        """Return all key-values"""
        return OPTIONS.get()

    def new_environ(self):
        """Return a new os.environ object"""
        env = os.environ.copy()
        i = self.options
        env.update({k: v for k, v in i.items() if isinstance(v, str)})
        return env

    # def llm(self, name: Optional[str] = None, provider: LLMType = LLMType.OPENAI) -> BaseLLM:
    #     """Return a LLM instance"""
    #     llm_config = self.config.get_llm_config(name, provider)
    #
    #     llm = create_llm_instance(llm_config)
    #     if llm.cost_manager is None:
    #         llm.cost_manager = self.cost_manager
    #     return llm


class ContextMixin:
    """Mixin class for configurable objects: Priority: more specific < parent"""

    _context: Optional[Context] = None

    def __init__(self, context: Optional[Context] = None):
        self._context = context

    def set_context(self, context: Optional[Context] = None):
        """Set parent context"""
        self._context = context

    @property
    def context(self):
        """Get config"""
        return self._context


# Global context, not in Env
context = Context()
