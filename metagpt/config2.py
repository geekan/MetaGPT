#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 01:25
# @Author  : alexanderwu
# @File    : config2.py

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
    """CLI parameters for MetaGPT.

    Attributes:
        project_path: The path to the project.
        project_name: The name of the project.
        inc: A boolean indicating if incremental mode is enabled.
        reqa_file: The path to the requirements file.
        max_auto_summarize_code: The maximum length for auto-summarized code.
        git_reinit: A boolean indicating if git should be reinitialized.
    """

    project_path: str = ""
    project_name: str = ""
    inc: bool = False
    reqa_file: str = ""
    max_auto_summarize_code: int = 0
    git_reinit: bool = False

    @model_validator(mode="after")
    def check_project_path(self):
        """Check project_path and project_name, enabling incremental mode if a project path is provided."""
        if self.project_path:
            self.inc = True
            self.project_name = self.project_name or Path(self.project_path).name
        return self


class Config(CLIParams, YamlModel):
    """Configurations for MetaGPT including various components and settings.

    Inherits CLI parameters and adds configurations for LLM, proxy, search, browser, mermaid, s3, redis, and more.

    Attributes:
        llm: Configuration for the language model.
        proxy: Proxy settings.
        search: Configuration for search functionality.
        browser: Browser configuration.
        mermaid: Configuration for Mermaid diagrams.
        s3: Configuration for S3 storage.
        redis: Configuration for Redis.
        repair_llm_output: Whether to repair LLM output.
        prompt_schema: The schema format for prompts.
        workspace: Workspace configuration.
        enable_longterm_memory: Whether to enable long-term memory.
        code_review_k_times: The number of times to review code.
        llm_for_researcher_summary: LLM used for researcher summary.
        llm_for_researcher_report: LLM used for researcher report.
        METAGPT_TEXT_TO_IMAGE_MODEL_URL: URL for the text-to-image model.
        language: The language setting.
        redis_key: The Redis key.
        mmdc: The Mermaid CLI.
        puppeteer_config: Configuration for Puppeteer.
        pyppeteer_executable_path: Executable path for Pyppeteer.
        IFLYTEK_APP_ID: App ID for iFlyTek.
        IFLYTEK_API_SECRET: API secret for iFlyTek.
        IFLYTEK_API_KEY: API key for iFlyTek.
        AZURE_TTS_SUBSCRIPTION_KEY: Subscription key for Azure TTS.
        AZURE_TTS_REGION: Region for Azure TTS.
        mermaid_engine: Engine used for Mermaid diagrams.
    """

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
        """Load default config with priority: env < default_config_paths. The latter config overwrites the former."""
        default_config_paths: List[Path] = [
            METAGPT_ROOT / "config/config2.yaml",
            Path.home() / ".metagpt/config2.yaml",
        ]

        dicts = [dict(os.environ)]
        dicts += [Config.read_yaml(path) for path in default_config_paths]
        final = merge_dict(dicts)
        return Config(**final)

    def update_via_cli(self, project_path, project_name, inc, reqa_file, max_auto_summarize_code):
        """Update configuration via CLI parameters."""

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
        """Get OpenAI LLMConfig by name. If no OpenAI, raise Exception."""
        if self.llm.api_type == LLMType.OPENAI:
            return self.llm
        return None

    def get_azure_llm(self) -> Optional[LLMConfig]:
        """Get Azure LLMConfig by name. If no Azure, raise Exception."""
        if self.llm.api_type == LLMType.AZURE:
            return self.llm
        return None


def merge_dict(dicts: Iterable[Dict]) -> Dict:
    """Merge multiple dicts into one, with the latter dict overwriting the former.

    Args:
        dicts: An iterable of dictionaries to merge.

    Returns:
        A single dictionary with the merged contents of the input dictionaries.
    """
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


config = Config.default()
