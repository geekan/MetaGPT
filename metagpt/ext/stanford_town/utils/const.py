#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from pathlib import Path

from metagpt.const import EXAMPLE_PATH

ST_ROOT_PATH = Path(__file__).parent.parent
STORAGE_PATH = EXAMPLE_PATH.joinpath("stanford_town/storage")
TEMP_STORAGE_PATH = EXAMPLE_PATH.joinpath("stanford_town/temp_storage")
MAZE_ASSET_PATH = ST_ROOT_PATH.joinpath("static_dirs/assets/the_ville")
PROMPTS_DIR = ST_ROOT_PATH.joinpath("prompts")

collision_block_id = "32125"
