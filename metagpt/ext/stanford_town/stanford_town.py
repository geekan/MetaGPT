#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : StanfordTown to works like SoftwareCompany

from typing import Any, Optional

from metagpt.context import Context
from metagpt.environment import StanfordTownEnv
from metagpt.ext.stanford_town.roles.st_role import STRole
from metagpt.ext.stanford_town.utils.const import MAZE_ASSET_PATH
from metagpt.logs import logger
from metagpt.team import Team


class StanfordTown(Team):
    env: Optional[StanfordTownEnv] = None

    def __init__(self, context: Context = None, **data: Any):
        super(Team, self).__init__(**data)
        ctx = context or Context()
        if not self.env:
            self.env = StanfordTownEnv(context=ctx, maze_asset_path=MAZE_ASSET_PATH)
        else:
            self.env.context = ctx  # The `env` object is allocated by deserialization

    async def hire(self, roles: list[STRole]):
        logger.warning(f"The Town add {len(roles)} roles, and start to operate.")
        super().hire(roles)
        for role in roles:
            await role.init_curr_tile()

    async def run(self, n_round: int = 3):
        """Run company until target round or no money"""
        while n_round > 0:
            n_round -= 1
            logger.debug(f"{n_round=}")
            self._check_balance()
            await self.env.run()

        # save simulation result including environment and roles after all rounds
        roles = self.env.get_roles()
        for profile, role in roles.items():
            role.save_into()

        return self.env.history
