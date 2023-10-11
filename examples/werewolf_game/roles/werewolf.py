from examples.werewolf_game.roles.base_player import BasePlayer
from examples.werewolf_game.actions import Speak, Impersonate

class Werewolf(BasePlayer):
    def __init__(
        self,
        name: str = "",
        profile: str = "Werewolf",
        special_action_names: list[str] = ["Hunt"],
        **kwargs,
    ):
        super().__init__(name, profile, special_action_names, **kwargs)

    async def _think(self):
        """狼人白天发言时需要伪装，与其他角色不同，因此需要重写_think"""
        await super()._think()
        if isinstance(self._rc.todo, Speak):
            self._rc.todo = Impersonate()
