#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent
STORAGE_PATH = ROOT_PATH.joinpath("storage")
MAZE_ASSET_PATH = ROOT_PATH.joinpath("static_dirs/assets/the_ville")
PROMPTS_DIR = ROOT_PATH.joinpath("prompts")

collision_block_id = "32125"
