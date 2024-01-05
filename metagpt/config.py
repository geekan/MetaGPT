#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provide configuration, singleton
@Modified By: mashenquan, 2023/11/27.
        1. According to Section 2.2.3.11 of RFC 135, add git repository support.
        2. Add the parameter `src_workspace` for the old version project path.
"""
import datetime
import json
import os
import warnings
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from metagpt.const import DEFAULT_WORKSPACE_ROOT, METAGPT_ROOT, OPTIONS
from metagpt.logs import logger
from metagpt.tools import SearchEngineType, WebBrowserEngineType
from metagpt.utils.common import require_python_version
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.singleton import Singleton


class NotConfiguredException(Exception):
    """Exception raised for errors in the configuration.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="The required configuration is not set"):
        self.message = message
        super().__init__(self.message)


class LLMProviderEnum(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    SPARK = "spark"
    ZHIPUAI = "zhipuai"
    FIREWORKS = "fireworks"
    OPEN_LLM = "open_llm"
    GEMINI = "gemini"
    METAGPT = "metagpt"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"

    def __missing__(self, key):
        return self.OPENAI


class Config(metaclass=Singleton):
    """
    Regular usage method:
    config = Config("config.yaml")
    secret_key = config.get_key("MY_SECRET_KEY")
    print("Secret key:", secret_key)
    """

    _instance = None
    home_yaml_file = Path.home() / ".metagpt/config.yaml"
    key_yaml_file = METAGPT_ROOT / "config/key.yaml"
    default_yaml_file = METAGPT_ROOT / "config/config.yaml"

    def __init__(self, yaml_file=default_yaml_file, cost_data=""):
        global_options = OPTIONS.get()
        # cli paras
        self.project_path = ""
        self.project_name = ""
        self.inc = False
        self.reqa_file = ""
        self.max_auto_summarize_code = 0
        self.git_reinit = False

        self._init_with_config_files_and_env(yaml_file)
        # The agent needs to be billed per user, so billing information cannot be destroyed when the session ends.
        self.cost_manager = CostManager(**json.loads(cost_data)) if cost_data else CostManager()
        self._update()
        global_options.update(OPTIONS.get())
        logger.debug("Config loading done.")

    def get_default_llm_provider_enum(self) -> LLMProviderEnum:
        """Get first valid LLM provider enum"""
        mappings = {
            LLMProviderEnum.OPENAI: bool(
                self._is_valid_llm_key(self.OPENAI_API_KEY) and not self.OPENAI_API_TYPE and self.OPENAI_API_MODEL
            ),
            LLMProviderEnum.ANTHROPIC: self._is_valid_llm_key(self.ANTHROPIC_API_KEY),
            LLMProviderEnum.ZHIPUAI: self._is_valid_llm_key(self.ZHIPUAI_API_KEY),
            LLMProviderEnum.FIREWORKS: self._is_valid_llm_key(self.FIREWORKS_API_KEY),
            LLMProviderEnum.OPEN_LLM: self._is_valid_llm_key(self.OPEN_LLM_API_BASE),
            LLMProviderEnum.GEMINI: self._is_valid_llm_key(self.GEMINI_API_KEY),
            LLMProviderEnum.METAGPT: bool(
                self._is_valid_llm_key(self.OPENAI_API_KEY) and self.OPENAI_API_TYPE == "metagpt"
            ),
            LLMProviderEnum.AZURE_OPENAI: bool(
                self._is_valid_llm_key(self.OPENAI_API_KEY)
                and self.OPENAI_API_TYPE == "azure"
                and self.DEPLOYMENT_NAME
                and self.OPENAI_API_VERSION
            ),
            LLMProviderEnum.OLLAMA: self._is_valid_llm_key(self.OLLAMA_API_BASE),
        }
        provider = None
        for k, v in mappings.items():
            if v:
                provider = k
                break
        if provider is None:
            if self.DEFAULT_PROVIDER:
                provider = LLMProviderEnum(self.DEFAULT_PROVIDER)
            else:
                raise NotConfiguredException("You should config a LLM configuration first")

        if provider is LLMProviderEnum.GEMINI and not require_python_version(req_version=(3, 10)):
            warnings.warn("Use Gemini requires Python >= 3.10")
        model_name = self.get_model_name(provider=provider)
        if model_name:
            logger.info(f"{provider} Model: {model_name}")
        if provider:
            logger.info(f"API: {provider}")
            return provider

    def get_model_name(self, provider=None) -> str:
        provider = provider or self.get_default_llm_provider_enum()
        model_mappings = {
            LLMProviderEnum.OPENAI: self.OPENAI_API_MODEL,
            LLMProviderEnum.AZURE_OPENAI: self.DEPLOYMENT_NAME,
        }
        return model_mappings.get(provider, "")

    @staticmethod
    def _is_valid_llm_key(k: str) -> bool:
        return bool(k and k != "YOUR_API_KEY")

    def _update(self):
        self.global_proxy = self._get("GLOBAL_PROXY")

        self.openai_api_key = self._get("OPENAI_API_KEY")
        self.anthropic_api_key = self._get("ANTHROPIC_API_KEY")
        self.zhipuai_api_key = self._get("ZHIPUAI_API_KEY")
        self.open_llm_api_base = self._get("OPEN_LLM_API_BASE")
        self.open_llm_api_model = self._get("OPEN_LLM_API_MODEL")
        self.fireworks_api_key = self._get("FIREWORKS_API_KEY")
        self.gemini_api_key = self._get("GEMINI_API_KEY")
        self.ollama_api_base = self._get("OLLAMA_API_BASE")
        self.ollama_api_model = self._get("OLLAMA_API_MODEL")

        if not self._get("DISABLE_LLM_PROVIDER_CHECK"):
            _ = self.get_default_llm_provider_enum()

        self.openai_base_url = self._get("OPENAI_BASE_URL")
        self.openai_proxy = self._get("OPENAI_PROXY") or self.global_proxy
        self.openai_api_type = self._get("OPENAI_API_TYPE")
        self.openai_api_version = self._get("OPENAI_API_VERSION")
        self.openai_api_rpm = self._get("RPM", 3)
        self.openai_api_model = self._get("OPENAI_API_MODEL", "gpt-4-1106-preview")
        self.max_tokens_rsp = self._get("MAX_TOKENS", 2048)
        self.deployment_name = self._get("DEPLOYMENT_NAME", "gpt-4")

        self.spark_appid = self._get("SPARK_APPID")
        self.spark_api_secret = self._get("SPARK_API_SECRET")
        self.spark_api_key = self._get("SPARK_API_KEY")
        self.domain = self._get("DOMAIN")
        self.spark_url = self._get("SPARK_URL")

        self.fireworks_api_base = self._get("FIREWORKS_API_BASE")
        self.fireworks_api_model = self._get("FIREWORKS_API_MODEL")

        self.claude_api_key = self._get("ANTHROPIC_API_KEY")
        self.serpapi_api_key = self._get("SERPAPI_API_KEY")
        self.serper_api_key = self._get("SERPER_API_KEY")
        self.google_api_key = self._get("GOOGLE_API_KEY")
        self.google_cse_id = self._get("GOOGLE_CSE_ID")
        self.search_engine = SearchEngineType(self._get("SEARCH_ENGINE", SearchEngineType.SERPAPI_GOOGLE))
        self.web_browser_engine = WebBrowserEngineType(self._get("WEB_BROWSER_ENGINE", WebBrowserEngineType.PLAYWRIGHT))
        self.playwright_browser_type = self._get("PLAYWRIGHT_BROWSER_TYPE", "chromium")
        self.selenium_browser_type = self._get("SELENIUM_BROWSER_TYPE", "chrome")

        self.long_term_memory = self._get("LONG_TERM_MEMORY", False)
        if self.long_term_memory:
            logger.warning("LONG_TERM_MEMORY is True")
        self.cost_manager.max_budget = self._get("MAX_BUDGET", 10.0)
        self.code_review_k_times = 2

        self.puppeteer_config = self._get("PUPPETEER_CONFIG", "")
        self.mmdc = self._get("MMDC", "mmdc")
        self.calc_usage = self._get("CALC_USAGE", True)
        self.model_for_researcher_summary = self._get("MODEL_FOR_RESEARCHER_SUMMARY")
        self.model_for_researcher_report = self._get("MODEL_FOR_RESEARCHER_REPORT")
        self.mermaid_engine = self._get("MERMAID_ENGINE", "nodejs")
        self.pyppeteer_executable_path = self._get("PYPPETEER_EXECUTABLE_PATH", "")

        workspace_uid = (
            self._get("WORKSPACE_UID") or f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[-8:]}"
        )
        self.repair_llm_output = self._get("REPAIR_LLM_OUTPUT", False)
        self.prompt_schema = self._get("PROMPT_FORMAT", "json")
        self.workspace_path = Path(self._get("WORKSPACE_PATH", DEFAULT_WORKSPACE_ROOT))
        val = self._get("WORKSPACE_PATH_WITH_UID")
        if val and val.lower() == "true":  # for agent
            self.workspace_path = self.workspace_path / workspace_uid
        self._ensure_workspace_exists()
        self.max_auto_summarize_code = self.max_auto_summarize_code or self._get("MAX_AUTO_SUMMARIZE_CODE", 1)
        self.timeout = int(self._get("TIMEOUT", 3))

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

    def _ensure_workspace_exists(self):
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"WORKSPACE_PATH set to {self.workspace_path}")

    def _init_with_config_files_and_env(self, yaml_file):
        """Load from config/key.yaml, config/config.yaml, and env in decreasing order of priority"""
        configs = dict(os.environ)

        for _yaml_file in [yaml_file, self.key_yaml_file, self.home_yaml_file]:
            if not _yaml_file.exists():
                continue

            # Load local YAML file
            with open(_yaml_file, "r", encoding="utf-8") as file:
                yaml_data = yaml.safe_load(file)
                if not yaml_data:
                    continue
                configs.update(yaml_data)
        OPTIONS.set(configs)

    @staticmethod
    def _get(*args, **kwargs):
        i = OPTIONS.get()
        return i.get(*args, **kwargs)

    def get(self, key, *args, **kwargs):
        """Retrieve values from config/key.yaml, config/config.yaml, and environment variables.
        Throw an error if not found."""
        value = self._get(key, *args, **kwargs)
        if value is None:
            raise ValueError(f"Key '{key}' not found in environment variables or in the YAML file")
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        OPTIONS.get()[name] = value

    def __getattr__(self, name: str) -> Any:
        i = OPTIONS.get()
        return i.get(name)

    def set_context(self, options: dict):
        """Update current config"""
        if not options:
            return
        opts = deepcopy(OPTIONS.get())
        opts.update(options)
        OPTIONS.set(opts)
        self._update()

    @property
    def options(self):
        """Return all key-values"""
        return OPTIONS.get()

    def new_environ(self):
        """Return a new os.environ object"""
        env = os.environ.copy()
        i = self.options
        env.update({k: v for k, v in i.items() if isinstance(v, str)})
        return env


CONFIG = Config()
