#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : data transform of mg <-> ga under storage

from .const import STORAGE_PATH
from .utils import read_json_file, write_json_file


def get_reverie_meta(sim_code: str) -> dict:
    meta_file_path = STORAGE_PATH.joinpath(sim_code).joinpath("reverie/meta.json")
    reverie_meta = read_json_file(meta_file_path)
    return reverie_meta
