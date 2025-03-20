#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path

from loguru import logger

import metagpt


def get_metagpt_package_root():
    """Get the root directory of the installed package."""
    package_root = Path(metagpt.__file__).parent.parent
    logger.info(f"Package root set to {str(package_root)}")
    return package_root


def get_metagpt_root():
    """Get the project root directory."""
    # Check if a project root is specified in the environment variable
    project_root_env = os.getenv("METAGPT_PROJECT_ROOT")
    if project_root_env:
        project_root = Path(project_root_env)
        logger.info(f"PROJECT_ROOT set from environment variable to {str(project_root)}")
    else:
        # Fallback to package root if no environment variable is set
        project_root = get_metagpt_package_root()
        for i in (".git", ".project_root", ".gitignore"):
            if (project_root / i).exists():
                break
        else:
            project_root = Path.cwd()

    return project_root


# METAGPT PROJECT ROOT AND VARS
CONFIG_ROOT = Path.home() / ".metagpt"
METAGPT_ROOT = get_metagpt_root()  # Dependent on METAGPT_PROJECT_ROOT

# REAL CONSTS
MEM_TTL = 24 * 30 * 3600

MESSAGE_ROUTE_FROM = "sent_from"
MESSAGE_ROUTE_TO = "send_to"
MESSAGE_ROUTE_CAUSE_BY = "cause_by"
MESSAGE_META_ROLE = "role"
MESSAGE_ROUTE_TO_ALL = "<all>"
MESSAGE_ROUTE_TO_NONE = "<none>"
MESSAGE_ROUTE_TO_SELF = "<self>"  # Add this tag to replace `ActionOutput`

CORE_REQUIREMENT_FILENAME = "requirement_core.txt"
BUGFIX_FILENAME = "bugfix.txt"

DEFAULT_LANGUAGE = "English"
DEFAULT_MAX_TOKENS = 1500
COMMAND_TOKENS = 500
DEFAULT_TOKEN_SIZE = 500

# format
BASE64_FORMAT = "base64"

# Message id
IGNORED_MESSAGE_ID = "0"

# Class Relationship
GENERALIZATION = "Generalize"
COMPOSITION = "Composite"
AGGREGATION = "Aggregate"

# Timeout
USE_CONFIG_TIMEOUT = 0  # Using llm.timeout configuration.
LLM_API_TIMEOUT = 300

# Assistant alias
ASSISTANT_ALIAS = "response"

# Markdown
MARKDOWN_TITLE_PREFIX = "## "

# Reporter
METAGPT_REPORTER_DEFAULT_URL = os.environ.get("METAGPT_REPORTER_URL", "")

# Metadata defines
AGENT = "agent"
IMAGES = "images"

DEFAULT_MIN_TOKEN_COUNT = 10000
DEFAULT_MAX_TOKEN_COUNT = 100000000
