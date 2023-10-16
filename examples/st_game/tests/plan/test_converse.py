#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of roles conversation

from typing import Tuple

from examples.st_game.roles.st_role import STRole
from examples.st_game.utils.const import STORAGE_PATH
from examples.st_game.utils.mg_ga_transform import get_reverie_meta
from examples.st_game.utils.utils import copy_folder
from examples.st_game.plan.converse import agent_conversation


def init_two_roles(fork_sim_code: str = "July1_the_ville_isabella_maria_klaus-step-3-8") -> Tuple["STRole"]:
    sim_code = "unittest_sim"

    copy_folder(str(STORAGE_PATH.joinpath(fork_sim_code)), str(STORAGE_PATH.joinpath(sim_code)))

    reverie_meta = get_reverie_meta(fork_sim_code)
    role_ir_name = "Isabella Rodriguez"
    role_km_name = "Klaus Mueller"

    role_ir = STRole(name=role_ir_name,
                     sim_code=sim_code,
                     profile=role_ir_name,
                     step=reverie_meta.get("step"),
                     start_date=reverie_meta.get("start_date"),
                     curr_time=reverie_meta.get("curr_time"),
                     sec_per_step=reverie_meta.get("sec_per_step"))

    role_km = STRole(name=role_km_name,
                     sim_code=sim_code,
                     profile=role_km_name,
                     step=reverie_meta.get("step"),
                     start_date=reverie_meta.get("start_date"),
                     curr_time=reverie_meta.get("curr_time"),
                     sec_per_step=reverie_meta.get("sec_per_step"))

    return role_ir, role_km


def test_agent_conversation():
    role_ir, role_km = init_two_roles()

    curr_chat = agent_conversation(role_ir, role_km)
    assert len(curr_chat) % 2 == 0

    meet = False
    for conv in curr_chat:
        if "Valentine's Day party" in conv[1]:
            # conv[0] speaker, conv[1] utterance
            meet = True
    assert meet
