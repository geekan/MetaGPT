#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 11:59
@Author  : alexanderwu
@File    : const.py'
@Modified By: mashenquan, 2023/8/28. Add 'OPTIONS', 'DEFAULT_LANGUAGE', 'DEFAULT_MAX_TOKENS'...
"""
import contextvars
from pathlib import Path


def get_project_root():
    """逐级向上寻找项目根目录"""
    current_path = Path.cwd()
    while True:
        if (
            (current_path / ".git").exists()
            or (current_path / ".project_root").exists()
            or (current_path / ".gitignore").exists()
        ):
            return current_path
        parent_path = current_path.parent
        if parent_path == current_path:
            raise Exception("Project root not found.")
        current_path = parent_path


PROJECT_ROOT = get_project_root()
DATA_PATH = PROJECT_ROOT / "data"
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
PROMPT_PATH = PROJECT_ROOT / "metagpt/prompts"
UT_PATH = PROJECT_ROOT / "data/ut"
SWAGGER_PATH = UT_PATH / "files/api/"
UT_PY_PATH = UT_PATH / "files/ut/"
API_QUESTIONS_PATH = UT_PATH / "files/question/"
YAPI_URL = "http://yapi.deepwisdomai.com/"
TMP = PROJECT_ROOT / "tmp"
RESEARCH_PATH = DATA_PATH / "research"

MEM_TTL = 24 * 30 * 3600

OPTIONS = contextvars.ContextVar("OPTIONS")
DEFAULT_LANGUAGE = "English"
DEFAULT_MAX_TOKENS = 1500
COMMAND_TOKENS = 500
BRAIN_MEMORY = "BRAIN_MEMORY"
SKILL_PATH = "SKILL_PATH"
SERPER_API_KEY = "SERPER_API_KEY"

# Key Definitions for MetaGPT LLM
METAGPT_API_MODEL = "METAGPT_API_MODEL"
METAGPT_API_KEY = "METAGPT_API_KEY"
METAGPT_API_BASE = "METAGPT_API_BASE"
METAGPT_API_TYPE = "METAGPT_API_TYPE"
METAGPT_API_VERSION = "METAGPT_API_VERSION"

# format
BASE64_FORMAT = "base64"

# REDIS
REDIS_KEY = "REDIS_KEY"
