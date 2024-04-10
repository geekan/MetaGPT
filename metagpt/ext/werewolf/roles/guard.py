from metagpt.ext.werewolf.roles.base_player import BasePlayer
from metagpt.environment.werewolf.const import RoleType


class Guard(BasePlayer):
    name: str = RoleType.GUARD.value
    profile: str = RoleType.GUARD.value
    special_action_names: list[str] = ["Protect"]
