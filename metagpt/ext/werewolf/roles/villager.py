from metagpt.ext.werewolf.roles.base_player import BasePlayer


class Villager(BasePlayer):
    name: str = "Villager"
    profile: str = "Villager"
    special_action_names: list[str] = []
