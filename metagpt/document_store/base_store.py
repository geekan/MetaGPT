#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/28 00:01
@Author  : alexanderwu
@File    : base_store.py
"""
from abc import ABC, abstractmethod
from pathlib import Path


class BaseStore(ABC):
    """FIXME: consider add_index, set_index and think about granularity."""

    @abstractmethod
    def search(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def write(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def add(self, *args, **kwargs):
        raise NotImplementedError


class LocalStore(BaseStore, ABC):
    def __init__(self, raw_data_path: Path, cache_dir: Path = None):
        if not raw_data_path:
            raise FileNotFoundError
        self.raw_data_path = raw_data_path
        self.fname = self.raw_data_path.stem
        if not cache_dir:
            cache_dir = raw_data_path.parent
        self.cache_dir = cache_dir
        self.store = self._load()
        if not self.store:
            self.store = self.write()

    def _get_index_and_store_fname(self, index_ext=".index", pkl_ext=".pkl"):
        index_file = self.cache_dir / f"{self.fname}{index_ext}"
        store_file = self.cache_dir / f"{self.fname}{pkl_ext}"
        return index_file, store_file

    @abstractmethod
    def _load(self):
        raise NotImplementedError

    @abstractmethod
    def _write(self, docs, metadatas):
        raise NotImplementedError
