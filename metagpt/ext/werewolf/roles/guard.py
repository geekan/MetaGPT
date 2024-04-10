from metagpt.environment.werewolf.const import RoleType
from metagpt.ext.werewolf.roles.base_player import BasePlayer


class Guard(BasePlayer):
    name: str = RoleType.GUARD.value
    profile: str = RoleType.GUARD.value
    special_action_names: list[str] = ["Protect"]
