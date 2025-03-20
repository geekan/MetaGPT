#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 01:25
@Author  : alexanderwu
@File    : config2.py
"""
import os
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from metagpt.configs.embedding_config import EmbeddingConfig
from metagpt.core.configs.llm_config import LLMConfig, LLMType
from metagpt.configs.omniparse_config import OmniParseConfig
from metagpt.configs.role_custom_config import RoleCustomConfig
from metagpt.configs.workspace_config import WorkspaceConfig
from metagpt.const import CONFIG_ROOT, METAGPT_ROOT
from metagpt.core.utils.yaml_model import YamlModel


class CLIParams(BaseModel):
    """CLI parameters"""

    project_path: str = ""
    project_name: str = ""
    inc: bool = False
    reqa_file: str = ""
    max_auto_summarize_code: int = 0
    git_reinit: bool = False

    @model_validator(mode="after")
    def check_project_path(self):
        """Check project_path and project_name"""
        if self.project_path:
            self.inc = True
            self.project_name = self.project_name or Path(self.project_path).name
        return self


class CoreConfig(CLIParams, YamlModel):
    """Configurations for MetaGPT"""

    # Key Parameters
    llm: LLMConfig

    # Global Proxy. Will be used if llm.proxy is not set
    proxy: str = ""

    # Misc Parameters
    repair_llm_output: bool = False
    prompt_schema: Literal["json", "markdown", "raw"] = "json"
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)

    @classmethod
    def from_home(cls, path):
        """Load config from ~/.metagpt/config2.yaml"""
        pathname = CONFIG_ROOT / path
        if not pathname.exists():
            return None
        return CoreConfig.from_yaml_file(pathname)

    @classmethod
    def default(cls, reload: bool = False, **kwargs) -> "CoreConfig":
        """Load default config
        - Priority: env < default_config_paths
        - Inside default_config_paths, the latter one overwrites the former one
        """
        default_config_paths = (
            METAGPT_ROOT / "config/config2.yaml",
            CONFIG_ROOT / "config2.yaml",
        )
        if reload or default_config_paths not in _CONFIG_CACHE:
            dicts = [dict(os.environ), *(CoreConfig.read_yaml(path) for path in default_config_paths), kwargs]
            final = merge_dict(dicts)
            _CONFIG_CACHE[default_config_paths] = CoreConfig(**final)
        return _CONFIG_CACHE[default_config_paths]

    @classmethod
    def from_llm_config(cls, llm_config: dict):
        """user config llm
        example:
        llm_config = {"api_type": "xxx", "api_key": "xxx", "model": "xxx"}
        gpt4 = CoreConfig.from_llm_config(llm_config)
        A = Role(name="A", profile="Democratic candidate", goal="Win the election", actions=[a1], watch=[a2], config=gpt4)
        """
        llm_config = LLMConfig.model_validate(llm_config)
        dicts = [dict(os.environ)]
        dicts += [{"llm": llm_config}]
        final = merge_dict(dicts)
        return CoreConfig(**final)

    def update_via_cli(self, project_path, project_name, inc, reqa_file, max_auto_summarize_code):
        """update config via cli"""

        # Use in the PrepareDocuments action according to Section 2.2.3.5.1 of RFC 135.
        if project_path:
            inc = True
            project_name = project_name or Path(project_path).name
        self.project_path = project_path
        self.project_name = project_name
        self.inc = inc
        self.reqa_file = reqa_file
        self.max_auto_summarize_code = max_auto_summarize_code


def merge_dict(dicts: Iterable[Dict]) -> Dict:
    """Merge multiple dicts into one, with the latter dict overwriting the former"""
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


_CONFIG_CACHE = {}