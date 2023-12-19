#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : graph_repository.py
@Desc    : Superclass for graph repository.
"""
from abc import ABC, abstractmethod
from enum import Enum


class GraphKeyword(Enum):
    IS = "is"
    CLASS = "class"
    FUNCTION = "function"
    GLOBAL_VARIABLE = "global_variable"
    CLASS_FUNCTION = "class_function"
    CLASS_PROPERTY = "class_property"
    HAS_CLASS = "has_class"


class GraphRepository(ABC):
    def __init__(self, name: str, **kwargs):
        self._repo_name = name
        self._kwargs = kwargs

    @abstractmethod
    async def insert(self, subject: str, predicate: str, object_: str):
        pass

    @abstractmethod
    async def upsert(self, subject: str, predicate: str, object_: str):
        pass

    @abstractmethod
    async def update(self, subject: str, predicate: str, object_: str):
        pass

    @property
    def name(self) -> str:
        return self._repo_name
