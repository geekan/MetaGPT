#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : data transform of mg <-> ga under storage

from pathlib import Path
from typing import Optional

from metagpt.ext.stanford_town.utils.const import STORAGE_PATH, TEMP_STORAGE_PATH
from metagpt.logs import logger
from metagpt.utils.common import read_json_file, write_json_file


def get_reverie_meta(sim_code: str) -> dict:
    meta_file_path = STORAGE_PATH.joinpath(sim_code).joinpath("reverie/meta.json")
    reverie_meta = read_json_file(meta_file_path)
    return reverie_meta


def save_movement(role_name: str, role_move: dict, step: int, sim_code: str, curr_time: str):
    movement_path = STORAGE_PATH.joinpath(f"{sim_code}/movement/{step}.json")
    if not movement_path.parent.exists():
        movement_path.parent.mkdir(exist_ok=True)
    if movement_path.exists():
        movement = read_json_file(movement_path)
    else:
        movement = {"persona": dict(), "meta": dict()}
    movement["persona"][role_name] = role_move
    movement["meta"]["curr_time"] = curr_time.strftime("%B %d, %Y, %H:%M:%S")

    write_json_file(movement_path, movement)
    logger.info(f"save_movement at step: {step}, curr_time: {movement['meta']['curr_time']}")


def save_environment(role_name: str, step: int, sim_code: str, movement: list[int]):
    environment_path = STORAGE_PATH.joinpath(f"{sim_code}/environment/{step}.json")
    if not environment_path.parent.exists():
        environment_path.parent.mkdir(exist_ok=True)
    if environment_path.exists():
        environment = read_json_file(environment_path)
    else:
        environment = {}

    environment[role_name] = {"maze": "the_ville", "x": movement[0], "y": movement[1]}
    write_json_file(environment_path, environment)
    logger.info(f"save_environment at step: {step}")


def get_role_environment(sim_code: str, role_name: str, step: int = 0) -> dict:
    env_path = STORAGE_PATH.joinpath(f"{sim_code}/environment/{step}.json")
    role_env = None
    if env_path.exists():
        env_info = read_json_file(env_path)
        role_env = env_info.get(role_name, None)

    return role_env


def write_curr_sim_code(curr_sim_code: dict, temp_storage_path: Optional[Path] = None):
    if temp_storage_path is None:
        temp_storage_path = TEMP_STORAGE_PATH
    else:
        temp_storage_path = Path(temp_storage_path)
    write_json_file(temp_storage_path.joinpath("curr_sim_code.json"), curr_sim_code)


def write_curr_step(curr_step: dict, temp_storage_path: Optional[Path] = None):
    if temp_storage_path is None:
        temp_storage_path = TEMP_STORAGE_PATH
    else:
        temp_storage_path = Path(temp_storage_path)
    write_json_file(temp_storage_path.joinpath("curr_step.json"), curr_step)
