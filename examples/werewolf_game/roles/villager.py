from examples.werewolf_game.roles.base_player import BasePlayer

class Villager(BasePlayer):
    def __init__(
        self,
        name: str = "",
        profile: str = "Villager",
        special_action_names: list[str] = [],
        **kwargs,
    ):
        super().__init__(name, profile, special_action_names, **kwargs)
