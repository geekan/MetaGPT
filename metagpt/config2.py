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

from pydantic import BaseModel, model_validator

from metagpt.configs.browser_config import BrowserConfig
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.configs.mermaid_config import MermaidConfig
from metagpt.configs.redis_config import RedisConfig
from metagpt.configs.s3_config import S3Config
from metagpt.configs.search_config import SearchConfig
from metagpt.configs.workspace_config import WorkspaceConfig
from metagpt.const import CONFIG_ROOT, METAGPT_ROOT
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
        return self


class Config(CLIParams, YamlModel):
    """Configurations for MetaGPT"""

    # Key Parameters
    llm: LLMConfig

    # Global Proxy. Will be used if llm.proxy is not set
    proxy: str = ""

    # Tool Parameters
    search: SearchConfig = SearchConfig()
    browser: BrowserConfig = BrowserConfig()
    mermaid: MermaidConfig = MermaidConfig()

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
    metagpt_tti_url: str = ""
    language: str = "English"
    redis_key: str = "placeholder"
    iflytek_app_id: str = ""
    iflytek_api_secret: str = ""
    iflytek_api_key: str = ""
    azure_tts_subscription_key: str = ""
    azure_tts_region: str = ""

    @classmethod
    def from_home(cls, path):
        """Load config from ~/.metagpt/config2.yaml"""
        pathname = CONFIG_ROOT / path
        if not pathname.exists():
            return None
        return Config.from_yaml_file(pathname)

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

    def get_openai_llm(self) -> Optional[LLMConfig]:
        """Get OpenAI LLMConfig by name. If no OpenAI, raise Exception"""
        if self.llm.api_type == LLMType.OPENAI:
            return self.llm
        return None

    def get_azure_llm(self) -> Optional[LLMConfig]:
        """Get Azure LLMConfig by name. If no Azure, raise Exception"""
        if self.llm.api_type == LLMType.AZURE:
            return self.llm
        return None


def merge_dict(dicts: Iterable[Dict]) -> Dict:
    """Merge multiple dicts into one, with the latter dict overwriting the former"""
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


config = Config.default()
