from examples.werewolf_game.roles.base_player import BasePlayer

class Guard(BasePlayer):
    def __init__(
        self,
        name: str = "",
        profile: str = "Guard",
        special_action_names: list[str] = ["Protect"],
        **kwargs,
    ):
        super().__init__(name, profile, special_action_names, **kwargs)
