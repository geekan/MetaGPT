#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the implement of serialization and deserialization

import copy
import pickle

from metagpt.utils.common import import_class


def resolve_ref(ref: str, defs: dict) -> dict:
    """
    Resolves a $ref to its definition in the provided defs dictionary.
    """
    ref_name = ref.split('/')[-1]  # Extract the reference name
    return defs.get(ref_name, {})


def get_type_from_property(property: dict, defs: dict):
    """
    Resolves the type of a property, handling both direct types and $ref.
    """
    # If directly provided a type, return it
    if 'type' in property:
        property_type = property['type']
        if property_type == 'string':
            return str
        elif property_type == 'array':
            # Check if 'items' has a direct 'type' or a '$ref'
            if 'type' in property['items']:
                # Direct item type (e.g. 'string')
                if property['items']['type'] == 'string':
                    return list[str]
                # Other types like 'object' or further nested array
                else:
                    nested_item_type = get_type_from_property(property['items']['items'], defs)
                    return list[nested_item_type]
            elif '$ref' in property['items']:
                # Resolve reference for items
                items_def = resolve_ref(property['items']['$ref'], defs)
                item_type = get_type_from_property(items_def, defs)
                return list[item_type]
        elif property_type == 'object':
            return dict  # Assuming an object can be represented as a dict
        # Add more types as necessary
        return property_type
    elif '$ref' in property:
        # Resolve reference
        ref_def = resolve_ref(property['$ref'], defs)
        return get_type_from_property(ref_def, defs)


def actionoutout_schema_to_mapping(schema: dict) -> dict:
    """
    Traverse the `properties` in the first level of the schema and create a mapping.
    This function handles `$ref` by looking up the definitions in `$defs` and resolves nested types.
    It is backward compatible with directly provided types in `items`.
    """
    mapping = {}
    defs = schema.get('$defs', {})

    for field, property in schema["properties"].items():
        prop_type = get_type_from_property(property, defs)
        mapping[field] = (prop_type, ...)

    return mapping


def actionoutput_mapping_to_str(mapping: dict) -> dict:
    new_mapping = {}
    for key, value in mapping.items():
        new_mapping[key] = str(value)
    return new_mapping


def actionoutput_str_to_mapping(mapping: dict) -> dict:
    new_mapping = {}
    for key, value in mapping.items():
        if value == "(<class 'str'>, Ellipsis)":
            new_mapping[key] = (str, ...)
        else:
            new_mapping[key] = eval(value)  # `"'(list[str], Ellipsis)"` to `(list[str], ...)`
    return new_mapping


def serialize_message(message: "Message"):
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
    message = pickle.loads(message_ser)
    if message.instruct_content:
        ic = message.instruct_content
        actionnode_class = import_class("ActionNode", "metagpt.actions.action_node")  # avoid circular import
        ic_obj = actionnode_class.create_model_class(class_name=ic["class"], mapping=ic["mapping"])
        ic_new = ic_obj(**ic["value"])
        message.instruct_content = ic_new

    return message
