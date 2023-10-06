#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 11:59
@Author  : alexanderwu
@File    : const.py
"""
from pathlib import Path


def get_project_root():
    """Search upwards to find the project root directory."""
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
TUTORIAL_PATH = DATA_PATH / "tutorial_docx"

SKILL_DIRECTORY = PROJECT_ROOT / "metagpt/skills"

MEM_TTL = 24 * 30 * 3600

### MineCraft ###
CKPT_DIR = PROJECT_ROOT / "metagpt/ckpt"
LOG_DIR = PROJECT_ROOT / "logs"

DEFAULT_WARMUP = {
            "context": 15,
            "biome": 10,
            "time": 15,
            "nearby_blocks": 0,
            "other_blocks": 10,
            "nearby_entities": 5,
            "health": 15,
            "hunger": 15,
            "position": 0,
            "equipment": 0,
            "inventory": 0,
            "optional_inventory_items": 7,
            "chests": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
        }

CURRICULUM_OB = [
            "context",
            "biome",
            "time",
            "nearby_blocks",
            "other_blocks",
            "nearby_entities",
            "health",
            "hunger",
            "position",
            "equipment",
            "inventory",
            "chests",
            "completed_tasks",
            "failed_tasks",
        ]


CORE_INVENTORY_ITEMS = r".*_log|.*_planks|stick|crafting_table|furnace"
r"|cobblestone|dirt|coal|.*_pickaxe|.*_sword|.*_axe",  # curriculum_agent: only show these items in inventory before optional_inventory_items reached in warm up