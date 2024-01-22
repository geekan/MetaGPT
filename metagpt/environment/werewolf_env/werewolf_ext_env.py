#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : The werewolf game external environment to integrate with

from enum import Enum

from pydantic import Field

from metagpt.env.base_env import ExtEnv, mark_as_readable, mark_as_writeable


class RoleState(Enum):
    ALIVE = "alive"
    KILLED = "killed"
    POISONED = "poisoned"
    SAVED = "saved"


class WerewolfExtEnv(ExtEnv):
    roles_state: dict[str, RoleState] = Field(default=dict(), description="the role's current state")

    @mark_as_readable
    def get_roles_status(self):
        pass

    @mark_as_writeable
    def wolf_kill_someone(self, role_name: str):
        pass

    @mark_as_writeable
    def witch_poison_someone(self, role_name: str = None):
        if not role_name:
            return

    @mark_as_writeable
    def witch_save_someone(self, role_name: str = None):
        if not role_name:
            return
