#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/8 11:38
@Author  : femto Zheng
@File    : test_custom_decoder.py
"""

import pytest

from metagpt.utils.custom_decoder import CustomDecoder


def test_parse_single_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = """{'a"
    b':'"title": "Reach and engagement of campaigns",
            "x-axis": "Low Reach --> High Reach",
            "y-axis": "Low Engagement --> High Engagement",
            "quadrant-1": "We should expand",
            "quadrant-2": "Need to promote",
            "quadrant-3": "Re-evaluate",
            "quadrant-4": "May be improved",
            "Campaign: A": [0.3, 0.6],
            "Campaign B": [0.45, 0.23],
            "Campaign C": [0.57, 0.69],
            "Campaign D": [0.78, 0.34],
            "Campaign E": [0.40, 0.34],
            "Campaign F": [0.35, 0.78],
            "Our Target Product": [0.5, 0.6]
            '
        }
    """
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert 'a"\n    b' in parsed_data

    input_data = """{
    'a': "
    b
"
}
"""
    with pytest.raises(Exception):
        parsed_data = decoder.decode(input_data)

    input_data = """{
    'a': '
    b
'
}
"""
    with pytest.raises(Exception):
        parsed_data = decoder.decode(input_data)


def test_parse_double_quote():
    decoder = CustomDecoder(strict=False)

    input_data = """{
    "a": "
    b
"
}
"""
    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "\n    b\n"

    input_data = """{
    "a": '
    b
'
}
"""
    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "\n    b\n"


def test_parse_triple_double_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = '{"""a""":"b"}'
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert "a" in parsed_data

    input_data = '{"""a""":"""b"""}'
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "b"

    input_data = "{\"\"\"a\"\"\": '''b'''}"
    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "b"


def test_parse_triple_single_quote():
    # Create a custom JSON decoder
    decoder = CustomDecoder(strict=False)
    # Your provided input with single-quoted strings and line breaks
    input_data = "{'''a''':'b'}"
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert "a" in parsed_data

    input_data = "{'''a''':'''b'''}"
    # Parse the JSON using the custom decoder

    parsed_data = decoder.decode(input_data)
    assert parsed_data["a"] == "b"
