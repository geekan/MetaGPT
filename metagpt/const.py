#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 11:59
@Author  : alexanderwu
@File    : const.py
@Modified By: mashenquan, 2023-11-1. According to Section 2.2.1 and 2.2.2 of RFC 116, added key definitions for
        common properties in the Message.
@Modified By: mashenquan, 2023-11-27. Defines file repository paths according to Section 2.2.3.4 of RFC 135.
@Modified By: mashenquan, 2023/12/5. Add directories for code summarization..
"""
import contextvars
import os
from pathlib import Path

from loguru import logger

import metagpt

OPTIONS = contextvars.ContextVar("OPTIONS")


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
    return project_root


# METAGPT PROJECT ROOT AND VARS

METAGPT_ROOT = get_metagpt_root()
DEFAULT_WORKSPACE_ROOT = METAGPT_ROOT / "workspace"

DATA_PATH = METAGPT_ROOT / "data"
RESEARCH_PATH = DATA_PATH / "research"
TUTORIAL_PATH = DATA_PATH / "tutorial_docx"
INVOICE_OCR_TABLE_PATH = DATA_PATH / "invoice_table"
UT_PATH = DATA_PATH / "ut"
SWAGGER_PATH = UT_PATH / "files/api/"
UT_PY_PATH = UT_PATH / "files/ut/"
API_QUESTIONS_PATH = UT_PATH / "files/question/"

TMP = METAGPT_ROOT / "tmp"

SOURCE_ROOT = METAGPT_ROOT / "metagpt"
PROMPT_PATH = SOURCE_ROOT / "prompts"
SKILL_DIRECTORY = SOURCE_ROOT / "skills"


# REAL CONSTS

MEM_TTL = 24 * 30 * 3600


MESSAGE_ROUTE_FROM = "sent_from"
MESSAGE_ROUTE_TO = "send_to"
MESSAGE_ROUTE_CAUSE_BY = "cause_by"
MESSAGE_META_ROLE = "role"
MESSAGE_ROUTE_TO_ALL = "<all>"
MESSAGE_ROUTE_TO_NONE = "<none>"

REQUIREMENT_FILENAME = "requirement.txt"
PACKAGE_REQUIREMENTS_FILENAME = "requirements.txt"

DOCS_FILE_REPO = "docs"
PRDS_FILE_REPO = "docs/prds"
SYSTEM_DESIGN_FILE_REPO = "docs/system_design"
TASK_FILE_REPO = "docs/tasks"
COMPETITIVE_ANALYSIS_FILE_REPO = "resources/competitive_analysis"
DATA_API_DESIGN_FILE_REPO = "resources/data_api_design"
SEQ_FLOW_FILE_REPO = "resources/seq_flow"
SYSTEM_DESIGN_PDF_FILE_REPO = "resources/system_design"
PRD_PDF_FILE_REPO = "resources/prd"
TASK_PDF_FILE_REPO = "resources/api_spec_and_tasks"
TEST_CODES_FILE_REPO = "tests"
TEST_OUTPUTS_FILE_REPO = "test_outputs"
CODE_SUMMARIES_FILE_REPO = "docs/code_summaries"
CODE_SUMMARIES_PDF_FILE_REPO = "resources/code_summaries"

YAPI_URL = "http://yapi.deepwisdomai.com/"
