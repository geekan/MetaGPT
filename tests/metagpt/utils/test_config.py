#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 11:19
@Author  : alexanderwu
@File    : test_config.py
@Modified By: mashenquan, 2013/8/20, add `test_options`
"""
from pathlib import Path

import pytest

from metagpt.config import Config


def test_config_class_is_singleton():
    config_1 = Config()
    config_2 = Config()
    assert config_1 == config_2


def test_config_class_get_key_exception():
    with pytest.raises(Exception) as exc_info:
        config = Config()
        config.get('wtf')
    assert str(exc_info.value) == "Key 'wtf' not found in environment variables or in the YAML file"


def test_config_yaml_file_not_exists():
    config = Config('wtf.yaml')
    with pytest.raises(Exception) as exc_info:
        config.get('OPENAI_BASE_URL')
    assert str(exc_info.value) == "Key 'OPENAI_BASE_URL' not found in environment variables or in the YAML file"


def test_options():
    filename = Path(__file__).resolve().parent.parent.parent.parent / "config/config.yaml"
    config = Config(filename)
    opts = config.options
    assert opts


if __name__ == '__main__':
    test_options()
