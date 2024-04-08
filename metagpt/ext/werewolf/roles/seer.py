from metagpt.ext.werewolf.roles.base_player import BasePlayer


class Seer(BasePlayer):
    name: str = "Seer"
    profile: str = "Seer"
    special_action_names: list[str] = ["Verify"]
