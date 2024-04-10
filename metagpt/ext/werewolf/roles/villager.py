from metagpt.environment.werewolf.const import RoleType
from metagpt.ext.werewolf.roles.base_player import BasePlayer


class Villager(BasePlayer):
    name: str = RoleType.VILLAGER.value
    profile: str = RoleType.VILLAGER.value
    special_action_names: list[str] = []
