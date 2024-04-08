from metagpt.ext.werewolf.actions.common_actions import NighttimeWhispers, Speak


class Hunt(NighttimeWhispers):
    name: str = "Hunt"


class Impersonate(Speak):
    """Action: werewolf impersonating a good guy in daytime speak"""

    STRATEGY: str = """
    Try continuously impersonating a role, such as Seer, Guard, Villager, etc., in order to mislead
    other players, make them trust you, and thus hiding your werewolf identity. However, pay attention to what your werewolf partner said, 
    DONT claim the same role as your werewolf partner. Remmber NOT to reveal your real identity as a werewolf!
    """

    name: str = "Impersonate"
