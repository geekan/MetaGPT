#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the implement of serialization and deserialization

import copy
import pickle

from metagpt.utils.common import import_class


def actionoutout_schema_to_mapping(schema: dict) -> dict:
    """Converts an action output schema to a mapping of field types.

    Args:
        schema: A dictionary representing the schema of an action's output.

    Returns:
        A dictionary mapping field names to their respective types and ellipsis.
    """
    mapping = dict()
    for field, property in schema["properties"].items():
        if property["type"] == "string":
            mapping[field] = (str, ...)
        elif property["type"] == "array" and property["items"]["type"] == "string":
            mapping[field] = (list[str], ...)
        elif property["type"] == "array" and property["items"]["type"] == "array":
            # here only consider the `list[list[str]]` situation
            mapping[field] = (list[list[str]], ...)
    return mapping


def actionoutput_mapping_to_str(mapping: dict) -> dict:
    """Converts a mapping of action output types to their string representation.

    Args:
        mapping: A dictionary mapping field names to their types.

    Returns:
        A dictionary with the same keys as the input, but values are the string representation of the types.
    """
    new_mapping = {}
    for key, value in mapping.items():
        new_mapping[key] = str(value)
    return new_mapping


def actionoutput_str_to_mapping(mapping: dict) -> dict:
    """Converts a string representation of a mapping back to its original form.

    Args:
        mapping: A dictionary with keys as field names and values as string representations of types.

    Returns:
        A dictionary mapping field names to their respective types and ellipsis.
    """
    new_mapping = {}
    for key, value in mapping.items():
        if value == "(<class 'str'>, Ellipsis)":
            new_mapping[key] = (str, ...)
        else:
            new_mapping[key] = eval(value)  # `"'(list[str], Ellipsis)"` to `(list[str], ...)`
    return new_mapping


def serialize_message(message: "Message"):
    """Serializes a message object for transmission or storage.

    Args:
        message: The message object to be serialized.

    Returns:
        A serialized representation of the message object.
    """
    message_cp = copy.deepcopy(message)  # avoid `instruct_content` value update by reference
    ic = message_cp.instruct_content
    if ic:
        # model create by pydantic create_model like `pydantic.main.prd`, can't pickle.dump directly
        schema = ic.model_json_schema()
        mapping = actionoutout_schema_to_mapping(schema)

        message_cp.instruct_content = {"class": schema["title"], "mapping": mapping, "value": ic.model_dump()}
    msg_ser = pickle.dumps(message_cp)

    return msg_ser


def deserialize_message(message_ser: str) -> "Message":
    """Deserializes a message from its serialized form back to a message object.

    Args:
        message_ser: The serialized message as a string.

    Returns:
        The deserialized message object.
    """
    message = pickle.loads(message_ser)
    if message.instruct_content:
        ic = message.instruct_content
        actionnode_class = import_class("ActionNode", "metagpt.actions.action_node")  # avoid circular import
        ic_obj = actionnode_class.create_model_class(class_name=ic["class"], mapping=ic["mapping"])
        ic_new = ic_obj(**ic["value"])
        message.instruct_content = ic_new

    return message
