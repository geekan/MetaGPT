#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
models_config.py

This module defines the ModelsConfig class for handling configuration of LLM models.

Attributes:
    CONFIG_ROOT (Path): Root path for configuration files.
    METAGPT_ROOT (Path): Root path for MetaGPT files.

Classes:
    ModelsConfig (YamlModel): Configuration class for LLM models.
"""
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import Field, field_validator

from metagpt.config2 import merge_dict
from metagpt.configs.llm_config import LLMConfig
from metagpt.const import CONFIG_ROOT, METAGPT_ROOT
from metagpt.utils.yaml_model import YamlModel


class ModelsConfig(YamlModel):
    """
    Configuration class for `models` in `config2.yaml`.

    Attributes:
        models (Dict[str, LLMConfig]): Dictionary mapping model names or types to LLMConfig objects.

    Methods:
        update_llm_model(cls, value): Validates and updates LLM model configurations.
        from_home(cls, path): Loads configuration from ~/.metagpt/config2.yaml.
        default(cls): Loads default configuration from predefined paths.
        get(self, name_or_type: str) -> Optional[LLMConfig]: Retrieves LLMConfig by name or API type.
    """

    models: Dict[str, LLMConfig] = Field(default_factory=dict)

    @field_validator("models", mode="before")
    @classmethod
    def update_llm_model(cls, value):
        """
        Validates and updates LLM model configurations.

        Args:
            value (Dict[str, Union[LLMConfig, dict]]): Dictionary of LLM configurations.

        Returns:
            Dict[str, Union[LLMConfig, dict]]: Updated dictionary of LLM configurations.
        """
        for key, config in value.items():
            if isinstance(config, LLMConfig):
                config.model = config.model or key
            elif isinstance(config, dict):
                config["model"] = config.get("model") or key
        return value

    @classmethod
    def from_home(cls, path):
        """
        Loads configuration from ~/.metagpt/config2.yaml.

        Args:
            path (str): Relative path to configuration file.

        Returns:
            Optional[ModelsConfig]: Loaded ModelsConfig object or None if file doesn't exist.
        """
        pathname = CONFIG_ROOT / path
        if not pathname.exists():
            return None
        return ModelsConfig.from_yaml_file(pathname)

    @classmethod
    def default(cls):
        """
        Loads default configuration from predefined paths.

        Returns:
            ModelsConfig: Default ModelsConfig object.
        """
        default_config_paths: List[Path] = [
            METAGPT_ROOT / "config/config2.yaml",
            CONFIG_ROOT / "config2.yaml",
        ]

        dicts = [ModelsConfig.read_yaml(path) for path in default_config_paths]
        final = merge_dict(dicts)
        return ModelsConfig(**final)

    def get(self, name_or_type: str) -> Optional[LLMConfig]:
        """
        Retrieves LLMConfig object by name or API type.

        Args:
            name_or_type (str): Name or API type of the LLM model.

        Returns:
            Optional[LLMConfig]: LLMConfig object if found, otherwise None.
        """
        if not name_or_type:
            return None
        model = self.models.get(name_or_type)
        if model:
            return model
        for m in self.models.values():
            if m.api_type == name_or_type:
                return m
        return None
