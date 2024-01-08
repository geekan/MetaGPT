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
from metagpt.const import OPTIONS
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import get_llm
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.git_repository import GitRepository


class AttrDict:
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
    kwargs: AttrDict = {}
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

    def llm(self, name: Optional[str] = None) -> BaseLLM:
        """Return a LLM instance"""
        llm = get_llm(self.config.get_llm_config(name))
        if llm.cost_manager is None:
            llm.cost_manager = self.cost_manager
        return llm


# Global context
context = Context()


if __name__ == "__main__":
    print(context.model_dump_json(indent=4))
    print(context.config.get_openai_llm())
