#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 19:07
# @Author  : alexanderwu
# @File    : s3_config.py

from metagpt.utils.yaml_model import YamlModelWithoutDefault


class S3Config(YamlModelWithoutDefault):
    """Configuration for S3 storage.

    Attributes:
        access_key: The access key for S3.
        secret_key: The secret key for S3.
        endpoint: The endpoint URL for S3.
        bucket: The bucket name in S3.
    """

    access_key: str
    secret_key: str
    endpoint: str
    bucket: str
