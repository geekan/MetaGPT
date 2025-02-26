from metagpt.environment.werewolf.const import RoleType
from metagpt.ext.werewolf.actions import Impersonate, Speak
from metagpt.ext.werewolf.roles.base_player import BasePlayer


class Werewolf(BasePlayer):
    name: str = RoleType.WEREWOLF.value
    profile: str = RoleType.WEREWOLF.value
    special_action_names: list[str] = ["Hunt"]

    async def _think(self):
        """狼人白天发言时需要伪装，与其他角色不同，因此需要重写_think"""
        await super()._think()
        if isinstance(self.rc.todo, Speak):
            self.rc.todo = Impersonate()
        return True
