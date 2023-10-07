#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : data transform of mg <-> ga under storage

import json

from metagpt.logs import logger

from examples.st_game.utils.const import STORAGE_PATH, TEMP_STORAGE_PATH
from examples.st_game.utils.utils import read_json_file, write_json_file


def get_reverie_meta(sim_code: str) -> dict:
    meta_file_path = STORAGE_PATH.joinpath(sim_code).joinpath("reverie/meta.json")
    reverie_meta = read_json_file(meta_file_path)
    return reverie_meta


def save_movement(role_name: str, role_move: dict, step: int, sim_code: str, curr_time: str):
    movement_path = STORAGE_PATH.joinpath(f"{sim_code}/movement/{step}.json")
    if not movement_path.parent.exists():
        movement_path.parent.mkdir(exist_ok=True)
    if movement_path.exists():
        with open(movement_path, "r") as fin:
            movement = json.load(fin)
    else:
        movement = {
            "persona": dict(),
            "meta": dict()
        }
    movement["persona"][role_name] = role_move
    movement["meta"]["curr_time"] = curr_time.strftime("%B %d, %Y, %H:%M:%S")

    write_json_file(movement_path, movement)
    logger.info(f"save_movement at step: {step}, curr_time: {movement['meta']['curr_time']}")


def get_role_environment(sim_code: str, role_name: str, step: int = 0) -> dict:
    env_path = STORAGE_PATH.joinpath(f"{sim_code}/environment/{step}.json")
    role_env = None
    if env_path.exists():
        environment = read_json_file(env_path)
        role_env = environment.get(role_name, None)

    return role_env


def write_curr_sim_code(curr_sim_code: dict):
    write_json_file(TEMP_STORAGE_PATH.joinpath("curr_sim_code.json"), curr_sim_code)


def write_curr_step(curr_step: dict):
    write_json_file(TEMP_STORAGE_PATH.joinpath("curr_step.json"), curr_step)
