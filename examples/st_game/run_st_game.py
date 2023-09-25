#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : entry of Stanford Town(ST/st) game

import asyncio
import fire

from stanford_town import StanfordTown
from roles.st_role import STRole


async def startup(idea: str,
                  investment: float = 30.0,
                  n_round: int = 500):

    # get role names from `storage/{simulation_name}/reverie/meta.json` and then init roles
    roles = []
    # TODO

    town = StanfordTown()
    town.wakeup_roles(roles)

    town.invest(investment)
    town.start_project()

    await town.run(n_round)


def main(idea: str,
         investment: float = 30.0,
         n_round: int = 500):
    """
    idea works as an `inner voice` to the first agent.
    """

    asyncio.run(startup(idea=idea,
                        investment=investment,
                        n_round=n_round))


if __name__ == "__main__":
    fire.Fire(main)
