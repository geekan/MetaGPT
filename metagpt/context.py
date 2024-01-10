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


class LLMInstance:
    """Mixin class for LLM"""

    # _config: Optional[Config] = None
    _llm_config: Optional[LLMConfig] = None
    _llm_instance: Optional[BaseLLM] = None

    def __init__(self, config: Config, name: Optional[str] = None, provider: LLMType = LLMType.OPENAI):
        """Use a LLM provider"""
        # 更新LLM配置
        self._llm_config = config.get_llm_config(name, provider)
        # 重置LLM实例
        self._llm_instance = None

    @property
    def instance(self) -> BaseLLM:
        """Return the LLM instance"""
        if not self._llm_instance and self._llm_config:
            self._llm_instance = create_llm_instance(self._llm_config)
        return self._llm_instance


class Context(BaseModel):
    """Env context for MetaGPT"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    kwargs: AttrDict = AttrDict()
    config: Config = Config.default()
    git_repo: Optional[GitRepository] = None
    src_workspace: Optional[Path] = None
    cost_manager: CostManager = CostManager()
    _llm: Optional[LLMInstance] = None

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

    def llm(self, name: Optional[str] = None, provider: LLMType = LLMType.OPENAI) -> BaseLLM:
        """Return a LLM instance"""
        llm = LLMInstance(self.config, name, provider).instance
        if llm.cost_manager is None:
            llm.cost_manager = self.cost_manager
        return llm


class ContextMixin(BaseModel):
    """Mixin class for context and config"""

    # Env/Role/Action will use this context as private context, or use self.context as public context
    _context: Optional[Context] = None
    # Env/Role/Action will use this config as private config, or use self.context.config as public config
    _config: Optional[Config] = None

    def __init__(self, context: Optional[Context] = None, config: Optional[Config] = None, **kwargs):
        """Initialize with config"""
        super().__init__(**kwargs)
        self.set_context(context)
        self.set_config(config)

    def set(self, k, v, override=False):
        """Set attribute"""
        if override or not self.__dict__.get(k):
            self.__dict__[k] = v

    def set_context(self, context: Context, override=True):
        """Set context"""
        self.set("_context", context, override)

    def set_config(self, config: Config, override=False):
        """Set config"""
        self.set("_config", config, override)

    @property
    def config(self):
        """Role config: role config > context config"""
        if self._config:
            return self._config
        return self.context.config

    @config.setter
    def config(self, config: Config):
        """Set config"""
        self.set_config(config)

    @property
    def context(self):
        """Role context: role context > context"""
        if self._context:
            return self._context
        return CONTEXT

    @context.setter
    def context(self, context: Context):
        """Set context"""
        self.set_context(context)


# Global context, not in Env
CONTEXT = Context()
