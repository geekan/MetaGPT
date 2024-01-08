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

from metagpt.config2 import Config
from metagpt.configs.llm_config import LLMType
from metagpt.const import OPTIONS
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import get_llm
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.git_repository import GitRepository


class AttrDict:
    """A dict-like object that allows access to keys as attributes."""

    def __init__(self, d=None):
        if d is None:
            d = {}
        self.__dict__["_dict"] = d

    def __getattr__(self, key):
        return self._dict.get(key, None)

    def __setattr__(self, key, value):
        self._dict[key] = value

    def __delattr__(self, key):
        if key in self._dict:
            del self._dict[key]
        else:
            raise AttributeError(f"No such attribute: {key}")


class Context:
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

    def llm(self, name: Optional[str] = None, provider: LLMType = LLMType.OPENAI) -> BaseLLM:
        """Return a LLM instance"""
        if provider:
            llm_configs = self.config.get_llm_configs_by_type(provider)
            if name:
                llm_configs = [c for c in llm_configs if c.name == name]

            if len(llm_configs) == 0:
                raise ValueError(f"Cannot find llm config with name {name} and provider {provider}")
            # return the first one if name is None, or return the only one
            llm_config = llm_configs[0]
        else:
            llm_config = self.config.get_llm_config(name)

        llm = get_llm(llm_config)
        if llm.cost_manager is None:
            llm.cost_manager = self.cost_manager
        return llm


# Global context
context = Context()


if __name__ == "__main__":
    # print(context.model_dump_json(indent=4))
    # print(context.config.get_openai_llm())
    ad = AttrDict({"name": "John", "age": 30})

    print(ad.name)  # Output: John
    print(ad.height)  # Output: None (因为height不存在)
