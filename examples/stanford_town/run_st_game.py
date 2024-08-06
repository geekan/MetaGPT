#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : entry of Stanford Town(ST/st) game
#           README see `metagpt/ext/stanford_town/README.md`

import asyncio
from typing import Optional

import fire

from metagpt.ext.stanford_town.roles.st_role import STRole
from metagpt.ext.stanford_town.stanford_town import StanfordTown
from metagpt.ext.stanford_town.utils.const import STORAGE_PATH
from metagpt.ext.stanford_town.utils.mg_ga_transform import (
    get_reverie_meta,
    write_curr_sim_code,
    write_curr_step,
)
from metagpt.ext.stanford_town.utils.utils import copy_folder
from metagpt.logs import logger


async def startup(
    idea: str, fork_sim_code: str, sim_code: str, temp_storage_path: str, investment: float = 30.0, n_round: int = 500
):
    town = StanfordTown()
    logger.info("StanfordTown init environment")

    # copy `storage/{fork_sim_code}` to `storage/{sim_code}`
    copy_folder(str(STORAGE_PATH.joinpath(fork_sim_code)), str(STORAGE_PATH.joinpath(sim_code)))

    # get role names from `storage/{simulation_name}/reverie/meta.json` and then init roles
    reverie_meta = get_reverie_meta(fork_sim_code)
    roles = []
    sim_path = STORAGE_PATH.joinpath(sim_code)
    sim_path.mkdir(exist_ok=True)
    for idx, role_name in enumerate(reverie_meta["persona_names"]):
        has_inner_voice = True if idx == 0 else False
        role = STRole(
            name=role_name,
            profile=role_name,
            sim_code=sim_code,
            step=reverie_meta.get("step", 0),
            start_time=reverie_meta.get("start_date"),
            curr_time=reverie_meta.get("curr_time"),
            sec_per_step=reverie_meta.get("sec_per_step"),
            has_inner_voice=has_inner_voice,
        )
        roles.append(role)

    # init temp_storage
    write_curr_sim_code({"sim_code": sim_code}, temp_storage_path)
    write_curr_step({"step": reverie_meta.get("step", 0)}, temp_storage_path)

    await town.hire(roles)

    town.invest(investment)
    town.run_project(idea)

    await town.run(n_round)


def main(
    idea: str,
    fork_sim_code: str,
    sim_code: str,
    temp_storage_path: Optional[str] = None,
    investment: float = 30.0,
    n_round: int = 500,
):
    """
    Args:
        idea: idea works as an `inner voice` to the first agent.
        fork_sim_code: old simulation name to start with, choose one inside `generative_agents/environment/frontend_server/storage/`
        sim_code: new simulation name to save simulation result
        temp_storage_path: generative_agents temp_storage path inside `environment/frontend_server` to interact.
        investment: the investment of running agents
        n_round: rounds to run agents
    """

    asyncio.run(
        startup(
            idea=idea,
            fork_sim_code=fork_sim_code,
            sim_code=sim_code,
            temp_storage_path=temp_storage_path,
            investment=investment,
            n_round=n_round,
        )
    )


if __name__ == "__main__":
    fire.Fire(main)
