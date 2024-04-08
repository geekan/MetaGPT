from metagpt.ext.werewolf.actions import Impersonate, Speak
from metagpt.ext.werewolf.roles.base_player import BasePlayer


class Werewolf(BasePlayer):
    name: str = "Werewolf"
    profile: str = "Werewolf"
    special_action_names: list[str] = ["Hunt"]

    async def _think(self):
        """狼人白天发言时需要伪装，与其他角色不同，因此需要重写_think"""
        await super()._think()
        if isinstance(self._rc.todo, Speak):
            self._rc.todo = Impersonate()
