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

from metagpt.configs.browser_config import BrowserConfig
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.configs.mermaid_config import MermaidConfig
from metagpt.configs.redis_config import RedisConfig
from metagpt.configs.s3_config import S3Config
from metagpt.configs.search_config import SearchConfig
from metagpt.configs.workspace_config import WorkspaceConfig
from metagpt.const import METAGPT_ROOT
from metagpt.utils.yaml_model import YamlModel


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


class Config(CLIParams, YamlModel):
    """Configurations for MetaGPT"""

    # Key Parameters
    llm: Dict[str, LLMConfig] = Field(default_factory=Dict)

    # Global Proxy. Will be used if llm.proxy is not set
    proxy: str = ""

    # Tool Parameters
    search: Dict[str, SearchConfig] = {}
    browser: Dict[str, BrowserConfig] = {"default": BrowserConfig()}
    mermaid: Dict[str, MermaidConfig] = {"default": MermaidConfig()}

    # Storage Parameters
    s3: Optional[S3Config] = None
    redis: Optional[RedisConfig] = None

    # Misc Parameters
    repair_llm_output: bool = False
    prompt_schema: Literal["json", "markdown", "raw"] = "json"
    workspace: WorkspaceConfig = WorkspaceConfig()
    enable_longterm_memory: bool = False
    code_review_k_times: int = 2

    # Will be removed in the future
    llm_for_researcher_summary: str = "gpt3"
    llm_for_researcher_report: str = "gpt3"
    METAGPT_TEXT_TO_IMAGE_MODEL_URL: str = ""
    language: str = "English"
    redis_key: str = "placeholder"

    @classmethod
    def default(cls):
        """Load default config
        - Priority: env < default_config_paths
        - Inside default_config_paths, the latter one overwrites the former one
        """
        default_config_paths: List[Path] = [
            METAGPT_ROOT / "config/config2.yaml",
            Path.home() / ".metagpt/config2.yaml",
        ]

        dicts = [dict(os.environ)]
        dicts += [Config.read_yaml(path) for path in default_config_paths]
        final = merge_dict(dicts)
        return Config(**final)

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

    def get_llm_config(self, name: Optional[str] = None) -> LLMConfig:
        """Get LLM instance by name"""
        if name is None:
            # Use the first LLM as default
            name = list(self.llm.keys())[0]
        if name not in self.llm:
            raise ValueError(f"LLM {name} not found in config")
        return self.llm[name]

    def get_llm_configs_by_type(self, llm_type: LLMType) -> List[LLMConfig]:
        """Get LLM instance by type"""
        return [v for k, v in self.llm.items() if v.api_type == llm_type]

    def get_llm_config_by_type(self, llm_type: LLMType) -> Optional[LLMConfig]:
        """Get LLM instance by type"""
        llm = self.get_llm_configs_by_type(llm_type)
        if llm:
            return llm[0]
        return None

    def get_openai_llm(self) -> Optional[LLMConfig]:
        """Get OpenAI LLMConfig by name. If no OpenAI, raise Exception"""
        return self.get_llm_config_by_type(LLMType.OPENAI)

    def get_azure_llm(self) -> Optional[LLMConfig]:
        """Get Azure LLMConfig by name. If no Azure, raise Exception"""
        return self.get_llm_config_by_type(LLMType.AZURE)


def merge_dict(dicts: Iterable[Dict]) -> Dict:
    """Merge multiple dicts into one, with the latter dict overwriting the former"""
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


class ConfigurableMixin:
    """Mixin class for configurable objects"""

    def __init__(self, config=None):
        self._config = config

    def try_set_parent_config(self, parent_config):
        """Try to set parent config if not set"""
        if self._config is None:
            self._config = parent_config

    @property
    def config(self):
        """Get config"""
        return self._config


config = Config.default()
