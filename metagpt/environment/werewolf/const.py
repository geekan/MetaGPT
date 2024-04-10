#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from enum import Enum

from metagpt.const import MESSAGE_ROUTE_TO_ALL


class RoleType(Enum):
    VILLAGER = "Villager"
    WEREWOLF = "Werewolf"
    GUARD = "Guard"
    SEER = "Seer"
    WITCH = "Witch"
    MODERATOR = "Moderator"


class RoleState(Enum):
    ALIVE = "alive"  # the role is alive
    DEAD = "dead"  # killed or poisoned
    KILLED = "killed"  # killed by werewolf or voting
    POISONED = "poisoned"  # killed by poison
    SAVED = "saved"  # saved by antidote
    PROTECTED = "projected"  # projected by guard


class RoleActionRes(Enum):
    SAVE = "save"
    PASS = "pass"  # ignore current action output


# the ordered rules by the moderator to announce to everyone each step
STEP_INSTRUCTIONS = {
    0: {
        "content": "It’s dark, everyone close your eyes. I will talk with you/your team secretly at night.",
        "send_to": {"Moderator"},  # for moderator to continue speaking
        "restricted_to": {},
    },
    1: {
        "content": "Guard, please open your eyes!",
        "send_to": {"Moderator"},  # for moderator to continue speaking
        "restricted_to": {},
    },
    2: {
        "content": """Guard, now tell me who you protect tonight?
                   You only choose one from the following living options please: {living_players}.
                   Or you can pass. For example: Protect ...""",
        "send_to": {"Guard"},
        "restricted_to": {"Moderator", "Guard"},
    },
    3: {"content": "Guard, close your eyes", "send_to": {"Moderator"}, "restricted_to": {}},
    4: {"content": "Werewolves, please open your eyes!", "send_to": {"Moderator"}, "restricted_to": {}},
    5: {
        "content": """Werewolves, I secretly tell you that {werewolf_players} are
                   all of the 2 werewolves! Keep in mind you are teammates. The rest players are not werewolves.
                   choose one from the following living options please:
                   {living_players}. For example: Kill ...""",
        "send_to": {"Werewolf"},
        "restricted_to": {"Moderator", "Werewolf"},
    },
    6: {"content": "Werewolves, close your eyes", "send_to": {"Moderator"}, "restricted_to": {}},
    7: {"content": "Witch, please open your eyes!", "send_to": {"Moderator"}, "restricted_to": {}},
    8: {
        "content": """Witch, tonight {player_hunted} has been killed by the werewolves.
                   You have a bottle of antidote, would you like to save him/her? If so, say "Save", else, say "Pass".""",
        "send_to": {"Witch"},
        "restricted_to": {"Moderator", "Witch"},
    },  # 要先判断女巫是否有解药，再去询问女巫是否使用解药救人
    9: {
        "content": """Witch, you also have a bottle of poison, would you like to use it to kill one of the living players?
                   Choose one from the following living options: {living_players}.
                   If so, say ONLY "Poison PlayerX", replace PlayerX with the actual player name, else, say "Pass".""",
        "send_to": {"Witch"},
        "restricted_to": {"Moderator", "Witch"},
    },  #
    10: {"content": "Witch, close your eyes", "send_to": {"Moderator"}, "restricted_to": {}},
    11: {"content": "Seer, please open your eyes!", "send_to": {"Moderator"}, "restricted_to": {}},
    12: {
        "content": """Seer, you can check one player's identity. Who are you going to verify its identity tonight?
                    Choose only one from the following living options:{living_players}.""",
        "send_to": {"Seer"},
        "restricted_to": {"Moderator", "Seer"},
    },
    13: {"content": "Seer, close your eyes", "send_to": {"Moderator"}, "restricted_to": {}},
    # The 1-st daytime
    14: {
        "content": """It's daytime. Everyone woke up except those who had been killed.""",
        "send_to": {"Moderator"},
        "restricted_to": {},
    },
    15: {"content": "{player_current_dead} was killed last night!", "send_to": {"Moderator"}, "restricted_to": {}},
    16: {
        "content": """Living players: {living_players}, now freely talk about the current situation based on your observation and
                    reflection with a few sentences. Decide whether to reveal your identity based on your reflection.""",
        "send_to": {MESSAGE_ROUTE_TO_ALL},  # send to all to speak in daytime
        "restricted_to": {},
    },
    17: {
        "content": """Now vote and tell me who you think is the werewolf. Don’t mention your role.
                    You only choose one from the following living options please:
                    {living_players}. Say ONLY: I vote to eliminate ...""",
        "send_to": {MESSAGE_ROUTE_TO_ALL},
        "restricted_to": {},
    },
    18: {"content": """{player_current_dead} was eliminated.""", "send_to": {"Moderator"}, "restricted_to": {}},
}
