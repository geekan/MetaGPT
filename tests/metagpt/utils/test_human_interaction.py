#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of human_interaction

from pydantic import BaseModel

from metagpt.utils.human_interaction import HumanInteraction


class InstructContent(BaseModel):
    test_field1: str = ""
    test_field2: list[str] = []


data_mapping = {"test_field1": (str, ...), "test_field2": (list[str], ...)}

human_interaction = HumanInteraction()


def test_input_num(mocker):
    mocker.patch("builtins.input", lambda _: "quit")

    interact_contents = human_interaction.interact_with_instruct_content(InstructContent(), data_mapping)
    assert len(interact_contents) == 0

    mocker.patch("builtins.input", lambda _: "1")
    input_num = human_interaction.input_num_until_valid(2)
    assert input_num == 1


def test_check_input_type():
    ret, _ = human_interaction.check_input_type(input_str="test string", req_type=str)
    assert ret

    ret, _ = human_interaction.check_input_type(input_str='["test string"]', req_type=list[str])
    assert ret

    ret, _ = human_interaction.check_input_type(input_str='{"key", "value"}', req_type=list[str])
    assert not ret


global_index = 0


def mock_input(*args, **kwargs):
    """there are multi input call, return it by global_index"""
    arr = ["1", '["test"]', "ignore", "quit"]
    global global_index
    global_index += 1
    if global_index == 3:
        raise EOFError()
    val = arr[global_index - 1]
    return val


def test_human_interact_valid_content(mocker):
    mocker.patch("builtins.input", mock_input)
    input_contents = HumanInteraction().interact_with_instruct_content(InstructContent(), data_mapping, "review")
    assert len(input_contents) == 1
    assert input_contents["test_field2"] == '["test"]'

    global global_index
    global_index = 0
    input_contents = HumanInteraction().interact_with_instruct_content(InstructContent(), data_mapping, "revise")
    assert len(input_contents) == 1
    assert input_contents["test_field2"] == ["test"]
