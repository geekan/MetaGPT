#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : entry of Stanford Town(ST/st) game

import asyncio
import fire

from stanford_town import StanfordTown
from roles.st_role import STRole
from utils.mg_ga_transform import get_reverie_meta
from utils.const import STORAGE_PATH


async def startup(idea: str,
                  fork_sim_code: str,
                  sim_code: str,
                  investment: float = 30.0,
                  n_round: int = 500):

    # get role names from `storage/{simulation_name}/reverie/meta.json` and then init roles
    reverie_meta = get_reverie_meta(fork_sim_code)
    roles = []
    sim_path = STORAGE_PATH.joinpath(sim_code)
    sim_path.mkdir(exist_ok=True)
    for idx, role_name in enumerate(reverie_meta["persona_names"]):
        role_stg_path = STORAGE_PATH.joinpath(fork_sim_code).joinpath(f"personas/{role_name}")
        has_inner_voice = True if idx == 0 else False
        role = STRole(name=role_name,
                      sim_code=sim_code,
                      profile=f"STMember_{idx}",
                      step=reverie_meta.get("step", 0),
                      start_date=reverie_meta.get("start_date"),
                      curr_time=reverie_meta.get("curr_time"),
                      sec_per_step=reverie_meta.get("sec_per_step"),
                      has_inner_voice=has_inner_voice)
        role.load_from(role_stg_path)
        roles.append(role)

    town = StanfordTown()
    town.wakeup_roles(roles)

    town.invest(investment)
    town.start_project(idea)

    await town.run(n_round)


def main(idea: str,
         fork_sim_code: str,
         sim_code: str,
         investment: float = 30.0,
         n_round: int = 500):
    """
    Args:
        idea: idea works as an `inner voice` to the first agent.
        fork_sim_code: old simulation name to start with
        sim_code: new simulation name to save simulation result
        investment: the investment of running agents
        n_round: rounds to run agents
    """

    asyncio.run(startup(idea=idea,
                        fork_sim_code=fork_sim_code,
                        sim_code=sim_code,
                        investment=investment,
                        n_round=n_round))


if __name__ == "__main__":
    fire.Fire(main)
