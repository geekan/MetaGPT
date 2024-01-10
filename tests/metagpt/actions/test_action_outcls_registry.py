#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of action_outcls_registry

from typing import List

from metagpt.actions.action_node import ActionNode


def test_action_outcls_registry():
    class_name = "test"
    out_mapping = {"field": (list[str], ...), "field1": (str, ...)}
    out_data = {"field": ["field value1", "field value2"], "field1": "field1 value1"}

    outcls = ActionNode.create_model_class(class_name, mapping=out_mapping)
    outinst = outcls(**out_data)

    outcls1 = ActionNode.create_model_class(class_name=class_name, mapping=out_mapping)
    outinst1 = outcls1(**out_data)
    assert outinst1 == outinst

    outcls2 = ActionNode(key="", expected_type=str, instruction="", example="").create_model_class(
        class_name, out_mapping
    )
    outinst2 = outcls2(**out_data)
    assert outinst2 == outinst

    out_mapping = {"field1": (str, ...), "field": (list[str], ...)}  # different order
    outcls3 = ActionNode.create_model_class(class_name=class_name, mapping=out_mapping)
    outinst3 = outcls3(**out_data)
    assert outinst3 == outinst

    out_mapping2 = {"field1": (str, ...), "field": (List[str], ...)}  # typing case
    outcls4 = ActionNode.create_model_class(class_name=class_name, mapping=out_mapping2)
    outinst4 = outcls4(**out_data)
    assert outinst4 == outinst

    out_data2 = {"field2": ["field2 value1", "field2 value2"], "field1": "field1 value1"}
    out_mapping = {"field1": (str, ...), "field2": (List[str], ...)}  # List first
    outcls5 = ActionNode.create_model_class(class_name, out_mapping)
    outinst5 = outcls5(**out_data2)

    out_mapping = {"field1": (str, ...), "field2": (list[str], ...)}
    outcls6 = ActionNode.create_model_class(class_name, out_mapping)
    outinst6 = outcls6(**out_data2)
    assert outinst5 == outinst6
