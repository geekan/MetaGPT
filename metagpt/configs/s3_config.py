#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 19:07
@Author  : alexanderwu
@File    : s3_config.py
"""
from metagpt.utils.yaml_model import YamlModelWithoutDefault


class S3Config(YamlModelWithoutDefault):
    access_key: str
    secret_key: str
    endpoint: str
    bucket: str
