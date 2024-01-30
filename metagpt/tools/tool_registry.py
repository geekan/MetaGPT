#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/01/12 17:07
@Author  : garylin2099
@File    : tool_registry.py
"""
import inspect
import os
import re
from collections import defaultdict

import yaml
from pydantic import BaseModel

from metagpt.const import TOOL_SCHEMA_PATH
from metagpt.logs import logger
from metagpt.tools.tool_convert import convert_code_to_tool_schema
from metagpt.tools.tool_data_type import Tool, ToolSchema, ToolType


class ToolRegistry(BaseModel):
    tools: dict = {}
    tool_types: dict = {}
    tools_by_types: dict = defaultdict(dict)  # two-layer k-v, {tool_type: {tool_name: {...}, ...}, ...}

    def register_tool_type(self, tool_type: ToolType, verbose: bool = False):
        self.tool_types[tool_type.name] = tool_type
        if verbose:
            logger.info(f"tool type {tool_type.name} registered")

    def register_tool(
        self,
        tool_name,
        tool_path,
        schema_path=None,
        tool_code="",
        tool_type="other",
        tool_source_object=None,
        include_functions=[],
        make_schema_if_not_exists=True,
        verbose=False,
    ):
        if self.has_tool(tool_name):
            return

        schema_path = schema_path or TOOL_SCHEMA_PATH / tool_type / f"{tool_name}.yml"

        if not os.path.exists(schema_path):
            if make_schema_if_not_exists:
                logger.warning(f"no schema found, will make schema at {schema_path}")
                schema_dict = make_schema(tool_source_object, include_functions, schema_path)
            else:
                logger.warning(f"no schema found at assumed schema_path {schema_path}, skip registering {tool_name}")
                return
        else:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_dict = yaml.safe_load(f)
        if not schema_dict:
            return
        schemas = schema_dict.get(tool_name) or list(schema_dict.values())[0]
        schemas["tool_path"] = tool_path  # corresponding code file path of the tool
        try:
            ToolSchema(**schemas)  # validation
        except Exception:
            pass
            # logger.warning(
            #     f"{tool_name} schema not conforms to required format, but will be used anyway. Mismatch: {e}"
            # )
        tool = Tool(name=tool_name, path=tool_path, schemas=schemas, code=tool_code)
        self.tools[tool_name] = tool
        self.tools_by_types[tool_type][tool_name] = tool
        if verbose:
            logger.info(f"{tool_name} registered")

    def has_tool(self, key: str) -> Tool:
        return key in self.tools

    def get_tool(self, key) -> Tool:
        return self.tools.get(key)

    def get_tools_by_type(self, key) -> dict[str, Tool]:
        return self.tools_by_types.get(key, {})

    def has_tool_type(self, key) -> bool:
        return key in self.tool_types

    def get_tool_type(self, key) -> ToolType:
        return self.tool_types.get(key)

    def get_tool_types(self) -> dict[str, ToolType]:
        return self.tool_types


# Registry instance
TOOL_REGISTRY = ToolRegistry()


def register_tool_type(cls):
    """register a tool type to registry"""
    TOOL_REGISTRY.register_tool_type(tool_type=cls())
    return cls


def register_tool(tool_name="", tool_type="other", schema_path=None, **kwargs):
    """register a tool to registry"""

    def decorator(cls, tool_name=tool_name):
        tool_name = tool_name or cls.__name__

        # Get the file path where the function / class is defined and the source code
        file_path = inspect.getfile(cls)
        if "metagpt" in file_path:
            file_path = re.search("metagpt.+", file_path).group(0)
        source_code = inspect.getsource(cls)

        TOOL_REGISTRY.register_tool(
            tool_name=tool_name,
            tool_path=file_path,
            schema_path=schema_path,
            tool_code=source_code,
            tool_type=tool_type,
            tool_source_object=cls,
            **kwargs,
        )
        return cls

    return decorator


def make_schema(tool_source_object, include, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)  # Create the necessary directories
    try:
        schema = convert_code_to_tool_schema(tool_source_object, include=include)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(schema, f, sort_keys=False)
        # import json
        # with open(str(path).replace("yml", "json"), "w", encoding="utf-8") as f:
        #     json.dump(schema, f, ensure_ascii=False, indent=4)
        logger.info(f"schema made at {path}")
    except Exception as e:
        schema = {}
        logger.error(f"Fail to make schema: {e}")

    return schema


def validate_tool_names(tools: list[str], return_tool_object=False) -> list[str]:
    valid_tools = []
    for tool_name in tools:
        if not TOOL_REGISTRY.has_tool(tool_name):
            logger.warning(
                f"Specified tool {tool_name} not found and was skipped. Check if you have registered it properly"
            )
        else:
            valid_tool = TOOL_REGISTRY.get_tool(tool_name) if return_tool_object else tool_name
            valid_tools.append(valid_tool)
    return valid_tools
