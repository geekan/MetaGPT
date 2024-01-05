#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 10:18
@Author  : alexanderwu
@File    : YamlModel.py
"""
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, model_validator


class YamlModel(BaseModel):
    extra_fields: Optional[Dict[str, str]] = None

    @classmethod
    def read_yaml(cls, file_path: Path) -> Dict:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)

    @classmethod
    def model_validate_yaml(cls, file_path: Path) -> "YamlModel":
        return cls(**cls.read_yaml(file_path))

    def model_dump_yaml(self, file_path: Path) -> None:
        with open(file_path, "w") as file:
            yaml.dump(self.model_dump(), file)


class YamlModelWithoutDefault(YamlModel):
    @model_validator(mode="before")
    @classmethod
    def check_not_default_config(cls, values):
        if any(["YOUR" in v for v in values]):
            raise ValueError("Please set your config in config.yaml")
        return values
