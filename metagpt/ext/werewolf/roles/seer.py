from metagpt.environment.werewolf.const import RoleType
from metagpt.ext.werewolf.roles.base_player import BasePlayer


class Seer(BasePlayer):
    name: str = RoleType.SEER.value
    profile: str = RoleType.SEER.value
    special_action_names: list[str] = ["Verify"]
