#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of MinecraftExtEnv


from metagpt.environment.minecraft.const import MC_CKPT_DIR
from metagpt.environment.minecraft.minecraft_ext_env import MinecraftExtEnv


def test_minecraft_ext_env():
    ext_env = MinecraftExtEnv()
    assert ext_env.server, f"{ext_env.server_host}:{ext_env.server_port}"
    assert MC_CKPT_DIR.joinpath("skill/code").exists()
    assert ext_env.warm_up.get("optional_inventory_items") == 7
