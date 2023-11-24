#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/16 16:34
# @Author  : lidanyang
# @File    : base.py
# @Desc    : Build base class to generate schema for tool
from typing import Any, List, Optional, get_type_hints


class NoDefault:
    """
    A class to represent a missing default value.

    This is used to distinguish between a default value of None and a missing default value.
    """
    pass


def tool_field(
    description: str, default: Any = NoDefault(), enum: Optional[List[Any]] = None, **kwargs
):
    """
    Create a field for a tool parameter.

    Args:
        description (str): A description of the field.
        default (Any, optional): The default value for the field. Defaults to None.
        enum (Optional[List[Any]], optional): A list of possible values for the field. Defaults to None.
        **kwargs: Additional keyword arguments.

    Returns:
        dict: A dictionary representing the field with provided attributes.
    """
    field_info = {
        "description": description,
        "default": default,
        "enum": enum,
    }
    field_info.update(kwargs)
    return field_info


class ToolSchema:
    @staticmethod
    def format_type(type_hint):
        """
        Format a type hint into a string representation.

        Args:
            type_hint (type): The type hint to format.

        Returns:
            str: A string representation of the type hint.
        """
        if isinstance(type_hint, type):
            # Handle built-in types separately
            if type_hint.__module__ == "builtins":
                return type_hint.__name__
            else:
                return f"{type_hint.__module__}.{type_hint.__name__}"
        elif hasattr(type_hint, "__origin__") and hasattr(type_hint, "__args__"):
            # Handle generic types (like List[int])
            origin_type = ToolSchema.format_type(type_hint.__origin__)
            args_type = ", ".join(
                [ToolSchema.format_type(t) for t in type_hint.__args__]
            )
            return f"{origin_type}[{args_type}]"
        else:
            return str(type_hint)

    @classmethod
    def schema(cls):
        """
        Generate a schema dictionary for the class.

        The schema includes the class name, description, and information about
        each class parameter based on type hints and field definitions.

        Returns:
            dict: A dictionary representing the schema of the class.
        """
        schema = {
            "name": cls.__name__,
            "description": cls.__doc__,
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
        type_hints = get_type_hints(cls)
        for attr, type_hint in type_hints.items():
            value = getattr(cls, attr, None)
            if isinstance(value, dict):
                # Process each attribute that is defined using the field function
                prop_info = {k: v for k, v in value.items() if v is not None or k == "default"}
                if isinstance(prop_info["default"], NoDefault):
                    del prop_info["default"]
                prop_info["type"] = ToolSchema.format_type(type_hint)
                schema["parameters"]["properties"][attr] = prop_info
                # Check for required fields
                if "default" not in prop_info:
                    schema["parameters"]["required"].append(attr)
        return schema
