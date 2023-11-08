#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provide configuration, singleton.
@Modified BY: mashenquan, 2023/8/28. Replace the global variable `CONFIG` with `ContextVar`.
"""
import datetime
import json
import os
from copy import deepcopy
from typing import Any
from uuid import uuid4

import httpx
import yaml

from metagpt.const import OPTIONS, PROJECT_ROOT, WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.tools import SearchEngineType, WebBrowserEngineType
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


class Config(metaclass=Singleton):
    """
    Usual Usage:
    config = Config("config.yaml")
    secret_key = config.get_key("MY_SECRET_KEY")
    print("Secret key:", secret_key)
    """

    _instance = None
    key_yaml_file = PROJECT_ROOT / "config/key.yaml"
    default_yaml_file = PROJECT_ROOT / "config/config.yaml"

    def __init__(self, yaml_file=default_yaml_file):
        self._init_with_config_files_and_env(yaml_file)
        self.cost_manager = CostManager(**json.loads(self.COST_MANAGER)) if self.COST_MANAGER else CostManager()

        logger.info("Config loading done.")
        self._update()

    def _update(self):
        self.global_proxy = self._get("GLOBAL_PROXY")
        self.openai_api_key = self._get("OPENAI_API_KEY")
        self.anthropic_api_key = self._get("Anthropic_API_KEY")
        if (not self.openai_api_key or "YOUR_API_KEY" == self.openai_api_key) and (
            not self.anthropic_api_key or "YOUR_API_KEY" == self.anthropic_api_key
        ):
            logger.warning("Set OPENAI_API_KEY or Anthropic_API_KEY first")
        self.openai_api_base = self._get("OPENAI_API_BASE")
        if not self.openai_api_base or "YOUR_API_BASE" == self.openai_api_base:
            openai_proxy = self._get("OPENAI_PROXY") or self.global_proxy
            if openai_proxy:
                # https://github.com/openai/openai-python#configuring-the-http-client
                # openai.proxy = openai_proxy
                pass
            else:
                logger.info("Set OPENAI_API_BASE in case of network issues")
        self.openai_api_type = self._get("OPENAI_API_TYPE")
        self.openai_api_version = self._get("OPENAI_API_VERSION")
        self.openai_api_rpm = self._get("RPM", 3)
        self.openai_api_model = self._get("OPENAI_API_MODEL", "gpt-4")
        self.max_tokens_rsp = self._get("MAX_TOKENS", 2048)
        self.deployment_id = self._get("DEPLOYMENT_ID")

        self.claude_api_key = self._get("Anthropic_API_KEY")
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

        self.puppeteer_config = self._get("PUPPETEER_CONFIG", "")
        self.mmdc = self._get("MMDC", "mmdc")
        self.calc_usage = self._get("CALC_USAGE", True)
        self.model_for_researcher_summary = self._get("MODEL_FOR_RESEARCHER_SUMMARY")
        self.model_for_researcher_report = self._get("MODEL_FOR_RESEARCHER_REPORT")

        workspace_uid = (
            self._get("WORKSPACE_UID") or f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[-8:]}"
        )
        self.workspace = WORKSPACE_ROOT / workspace_uid

    def _init_with_config_files_and_env(self, yaml_file):
        """从config/key.yaml / config/config.yaml / env三处按优先级递减加载"""
        configs = dict(os.environ)

        for _yaml_file in [yaml_file, self.key_yaml_file]:
            if not _yaml_file.exists():
                continue

            # 加载本地 YAML 文件
            with open(_yaml_file, "r", encoding="utf-8") as file:
                yaml_data = yaml.safe_load(file)
                if not yaml_data:
                    continue
                configs.update(yaml_data)
        OPTIONS.set(configs)

    @staticmethod
    def _get(*args, **kwargs):
        m = OPTIONS.get()
        return m.get(*args, **kwargs)

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
        m = OPTIONS.get()
        return m.get(name)

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

    @staticmethod
    def get_openai_options():
        options = {}
        if CONFIG.openai_api_base:
            options["base_url"] = CONFIG.openai_api_base
        if CONFIG.OPENAI_PROXY:
            options["http_client"] = httpx.Client(
                proxies=CONFIG.OPENAI_PROXY,
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),
            )
        return options


CONFIG = Config()
