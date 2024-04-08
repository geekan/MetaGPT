from metagpt.ext.werewolf.roles.base_player import BasePlayer


class Guard(BasePlayer):
    name: str = "Guard"
    profile: str = "Guard"
    special_action_names: list[str] = ["Protect"]
