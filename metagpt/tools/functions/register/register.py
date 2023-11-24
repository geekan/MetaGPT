#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/16 16:38
# @Author  : lidanyang
# @File    : register.py
# @Desc    :
from typing import Type, Optional, Callable, Dict, Union, List

from metagpt.tools.functions.schemas.base import ToolSchema


class FunctionRegistry:
    def __init__(self):
        self.functions: Dict[str, Dict[str, Dict]] = {}

    def register(self, module: str, tool_schema: Type[ToolSchema]) -> Callable:

        def wrapper(func: Callable) -> Callable:
            module_registry = self.functions.setdefault(module, {})

            if func.__name__ in module_registry:
                raise ValueError(f"Function {func.__name__} is already registered in {module}")

            schema = tool_schema.schema()
            schema["name"] = func.__name__
            module_registry[func.__name__] = {
                "func": func,
                "schema": schema,
            }
            return func

        return wrapper

    def get(self, module: str, name: str) -> Optional[Union[Callable, Dict]]:
        """Get function by module and name"""
        module_registry = self.functions.get(module, {})
        return module_registry.get(name)

    def get_by_name(self, name: str) -> Optional[Dict]:
        """Get function by name"""
        for module_registry in self.functions.values():
            if name in module_registry:
                return module_registry.get(name, {})

    def get_all_by_module(self, module: str) -> Optional[Dict]:
        """Get all functions by module"""
        return self.functions.get(module, {})

    def get_schema(self, module: str, name: str) -> Optional[Dict]:
        """Get schema by module and name"""
        module_registry = self.functions.get(module, {})
        return module_registry.get(name, {}).get("schema")

    def get_schemas(self, module: str, names: List[str]) -> List[Dict]:
        """Get schemas by module and names"""
        module_registry = self.functions.get(module, {})
        return [module_registry.get(name, {}).get("schema") for name in names]

    def get_all_schema_by_module(self, module: str) -> List[Dict]:
        """Get all schemas by module"""
        module_registry = self.functions.get(module, {})
        return [v.get("schema") for v in module_registry.values()]


registry = FunctionRegistry()
