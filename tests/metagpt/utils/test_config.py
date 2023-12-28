#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 11:19
@Author  : alexanderwu
@File    : test_config.py
@Modified By: mashenquan, 2013/8/20, Add `test_options`; remove global configuration `CONFIG`, enable configuration support for business isolation.
"""
from pathlib import Path

import pytest

from metagpt.config import Config


def test_config_class_get_key_exception():
    with pytest.raises(Exception) as exc_info:
        config = Config()
        config.get("wtf")
    assert str(exc_info.value) == "Key 'wtf' not found in environment variables or in the YAML file"


def test_config_yaml_file_not_exists():
    # FIXME: 由于这里是单例，所以会导致Config重新创建失效。后续要将Config改为非单例模式。
    _ = Config("wtf.yaml")
    # with pytest.raises(Exception) as exc_info:
    #     config.get("OPENAI_BASE_URL")
    # assert str(exc_info.value) == "Set OPENAI_API_KEY or Anthropic_API_KEY first"


def test_options():
    filename = Path(__file__).resolve().parent.parent.parent.parent / "config/config.yaml"
    config = Config(filename)
    assert config.options


if __name__ == "__main__":
    test_options()
