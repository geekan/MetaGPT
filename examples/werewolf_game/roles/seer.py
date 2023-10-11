from examples.werewolf_game.roles.base_player import BasePlayer

class Seer(BasePlayer):
    def __init__(
            self,
            name: str = "",
            profile: str = "Seer",
            special_action_names: list[str] = ["Verify"],
            **kwargs,
    ):
        super().__init__(name, profile, special_action_names, **kwargs)
