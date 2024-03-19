#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of MincraftExtEnv


from metagpt.environment.mincraft_env.const import MC_CKPT_DIR
from metagpt.environment.mincraft_env.mincraft_ext_env import MincraftExtEnv


def test_mincraft_ext_env():
    ext_env = MincraftExtEnv()
    assert ext_env.server, f"{ext_env.server_host}:{ext_env.server_port}"
    assert MC_CKPT_DIR.joinpath("skill/code").exists()
    assert ext_env.warm_up.get("optional_inventory_items") == 7
