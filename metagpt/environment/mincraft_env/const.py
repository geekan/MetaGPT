#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from metagpt.const import METAGPT_ROOT

# For Mincraft Game Agent
MC_CKPT_DIR = METAGPT_ROOT / "data/mincraft/ckpt"
MC_LOG_DIR = METAGPT_ROOT / "logs"
MC_DEFAULT_WARMUP = {
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
MC_CURRICULUM_OB = [
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
MC_CORE_INVENTORY_ITEMS = r".*_log|.*_planks|stick|crafting_table|furnace"
r"|cobblestone|dirt|coal|.*_pickaxe|.*_sword|.*_axe",  # curriculum_agent: only show these items in inventory before optional_inventory_items reached in warm up
