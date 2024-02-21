#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 10:18
# @Author  : alexanderwu
# @File    : YamlModel.py

from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, model_validator


class YamlModel(BaseModel):
    """Base class for yaml model.

    Attributes:
        extra_fields: Optional dictionary to store additional fields not explicitly defined in the model.
    """

    extra_fields: Optional[Dict[str, str]] = None

    @classmethod
    def read_yaml(cls, file_path: Path, encoding: str = "utf-8") -> Dict:
        """Read yaml file and return a dict.

        Args:
            file_path: The path to the yaml file.
            encoding: The encoding format used to open the file.

        Returns:
            A dictionary representation of the yaml file.
        """
        if not file_path.exists():
            return {}
        with open(file_path, "r", encoding=encoding) as file:
            return yaml.safe_load(file)

    @classmethod
    def from_yaml_file(cls, file_path: Path) -> "YamlModel":
        """Read yaml file and return a YamlModel instance.

        Args:
            file_path: The path to the yaml file.

        Returns:
            An instance of YamlModel.
        """
        return cls(**cls.read_yaml(file_path))

    def to_yaml_file(self, file_path: Path, encoding: str = "utf-8") -> None:
        """Dump YamlModel instance to yaml file.

        Args:
            file_path: The path where the yaml file will be saved.
            encoding: The encoding format used to save the file.
        """
        with open(file_path, "w", encoding=encoding) as file:
            yaml.dump(self.model_dump(), file)


class YamlModelWithoutDefault(YamlModel):
    """YamlModel without default values."""

    @model_validator(mode="before")
    @classmethod
    def check_not_default_config(cls, values):
        """Check if there is any default config in config2.yaml.

        Args:
            values: The values to be checked for default configurations.

        Returns:
            The validated values without default configurations.

        Raises:
            ValueError: If any default configuration is found.
        """
        if any(["YOUR" in v for v in values]):
            raise ValueError("Please set your config in config2.yaml")
        return values
