#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : The werewolf game external environment to integrate with

import random
import re
from collections import Counter
from enum import Enum
from typing import Callable, Optional

from pydantic import ConfigDict, Field

from metagpt.environment.base_env import ExtEnv, mark_as_readable, mark_as_writeable
from metagpt.logs import logger


class RoleState(Enum):
    ALIVE = "alive"  # the role is alive
    KILLED = "killed"  # the role is killed by werewolf or voting
    POISONED = "poisoned"  # the role is killed by posion
    SAVED = "saved"  # the role is saved by antidote


# the ordered rules by the moderator to announce to everyone each step
STEP_INSTRUCTIONS = {
    0: {
        "content": "It’s dark, everyone close your eyes. I will talk with you/your team secretly at night.",
        "send_to": "Moderator",  # for moderator to continuen speaking
        "restricted_to": "",
    },
    1: {
        "content": "Guard, please open your eyes!",
        "send_to": "Moderator",  # for moderator to continuen speaking
        "restricted_to": "",
    },
    2: {
        "content": """Guard, now tell me who you protect tonight?
                   You only choose one from the following living options please: {living_players}.
                   Or you can pass. For example: Protect ...""",
        "send_to": "Guard",
        "restricted_to": "Moderator,Guard",
    },
    3: {"content": "Guard, close your eyes", "send_to": "Moderator", "restricted_to": ""},
    4: {"content": "Werewolves, please open your eyes!", "send_to": "Moderator", "restricted_to": ""},
    5: {
        "content": """Werewolves, I secretly tell you that {werewolf_players} are
                   all of the 2 werewolves! Keep in mind you are teammates. The rest players are not werewolves.
                   choose one from the following living options please:
                   {living_players}. For example: Kill ...""",
        "send_to": "Werewolf",
        "restricted_to": "Moderator,Werewolf",
    },
    6: {"content": "Werewolves, close your eyes", "send_to": "Moderator", "restricted_to": ""},
    7: {"content": "Witch, please open your eyes!", "send_to": "Moderator", "restricted_to": ""},
    8: {
        "content": """Witch, tonight {player_hunted} has been killed by the werewolves.
                   You have a bottle of antidote, would you like to save him/her? If so, say "Save", else, say "Pass".""",
        "send_to": "Witch",
        "restricted_to": "Moderator,Witch",
    },  # 要先判断女巫是否有解药，再去询问女巫是否使用解药救人
    9: {
        "content": """Witch, you also have a bottle of poison, would you like to use it to kill one of the living players?
                   Choose one from the following living options: {living_players}.
                   If so, say ONLY "Poison PlayerX", replace PlayerX with the actual player name, else, say "Pass".""",
        "send_to": "Witch",
        "restricted_to": "Moderator,Witch",
    },  #
    10: {"content": "Witch, close your eyes", "send_to": "Moderator", "restricted_to": ""},
    11: {"content": "Seer, please open your eyes!", "send_to": "Moderator", "restricted_to": ""},
    12: {
        "content": """Seer, you can check one player's identity. Who are you going to verify its identity tonight?
                    Choose only one from the following living options:{living_players}.""",
        "send_to": "Seer",
        "restricted_to": "Moderator,Seer",
    },
    13: {"content": "Seer, close your eyes", "send_to": "Moderator", "restricted_to": ""},
    # The 1-st daytime
    14: {
        "content": """It's daytime. Everyone woke up except those who had been killed.""",
        "send_to": "Moderator",
        "restricted_to": "",
    },
    15: {"content": "{player_current_dead} was killed last night!", "send_to": "Moderator", "restricted_to": ""},
    16: {
        "content": """Living players: {living_players}, now freely talk about the current situation based on your observation and
                    reflection with a few sentences. Decide whether to reveal your identity based on your reflection.""",
        "send_to": "",  # send to all to speak in daytime
        "restricted_to": "",
    },
    17: {
        "content": """Now vote and tell me who you think is the werewolf. Don’t mention your role.
                    You only choose one from the following living options please:
                    {living_players}. Say ONLY: I vote to eliminate ...""",
        "send_to": "",
        "restricted_to": "",
    },
    18: {"content": """{player_current_dead} was eliminated.""", "send_to": "Moderator", "restricted_to": ""},
}


class WerewolfExtEnv(ExtEnv):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    roles_state: dict[str, RoleState] = Field(default=dict(), description="the role's current state by role_name")

    step_idx: int = Field(default=0)  # the current step of current round
    eval_step_idx: int = Field(default=0)
    per_round_steps: int = Field(default=len(STEP_INSTRUCTIONS))

    # game global states
    game_setup: str = Field(default="", description="game setup including role and its num")
    living_players: list[str] = Field(default=[])
    werewolf_players: list[str] = Field(default=[])
    villager_players: list[str] = Field(default=[])
    special_role_players: list[str] = Field(default=[])
    winner: Optional[str] = Field(default=None)
    win_reason: Optional[str] = Field(default=None)
    witch_poison_left: int = Field(default=1)
    witch_antidote_left: int = Field(default=1)

    # game current round states, a round is from closing your eyes to the next time you close your eyes
    player_hunted: Optional[str] = Field(default=None)
    player_protected: Optional[str] = Field(default=None)
    is_hunted_player_saved: bool = Field(default=False)
    player_poisoned: Optional[str] = Field(default=None)
    player_current_dead: list[str] = Field(default=[])

    def parse_game_setup(self, game_setup: str):
        self.game_setup = game_setup
        self.living_players = re.findall(r"Player[0-9]+", game_setup)
        self.werewolf_players = re.findall(r"Player[0-9]+: Werewolf", game_setup)
        self.werewolf_players = [p.replace(": Werewolf", "") for p in self.werewolf_players]
        self.villager_players = re.findall(r"Player[0-9]+: Villager", game_setup)
        self.villager_players = [p.replace(": Villager", "") for p in self.villager_players]
        self.special_role_players = [
            p for p in self.living_players if p not in self.werewolf_players + self.villager_players
        ]

        # init role state
        self.roles_state = {player_name: RoleState.ALIVE for player_name in self.living_players}

    @mark_as_readable
    def init_game_setup(
        self,
        role_uniq_objs: list[object],
        num_villager: int = 2,
        num_werewolf: int = 2,
        shuffle=True,
        add_human=False,
        use_reflection=True,
        use_experience=False,
        use_memory_selection=False,
        new_experience_version="",
        prepare_human_player=Callable,
    ) -> tuple[str, list]:
        role_objs = []
        for role_obj in role_uniq_objs:
            if str(role_obj) == "Villager":
                role_objs.extend([role_obj] * num_villager)
            elif str(role_obj) == "Werewolf":
                role_objs.extend([role_obj] * num_werewolf)
            else:
                role_objs.append(role_obj)
        if shuffle:
            random.shuffle(len(role_objs))
        if add_human:
            assigned_role_idx = random.randint(0, len(role_objs) - 1)
            assigned_role = role_objs[assigned_role_idx]
            role_objs[assigned_role_idx] = prepare_human_player(assigned_role)  # TODO

        players = [
            role(
                name=f"Player{i + 1}",
                use_reflection=use_reflection,
                use_experience=use_experience,
                use_memory_selection=use_memory_selection,
                new_experience_version=new_experience_version,
            )
            for i, role in enumerate(role_objs)
        ]

        if add_human:
            logger.info(f"You are assigned {players[assigned_role_idx].name}({players[assigned_role_idx].profile})")

        game_setup = ["Game setup:"] + [f"{player.name}: {player.profile}," for player in players]
        game_setup = "\n".join(game_setup)

        return game_setup, players

    @mark_as_readable
    def curr_step_instruction(self) -> dict:
        step_idx = self.step_idx % len(STEP_INSTRUCTIONS)
        instruction = STEP_INSTRUCTIONS[step_idx]
        self.step_idx += 1
        return instruction

    @mark_as_writeable
    def update_players_state(self, player_names: list[str], state: RoleState = RoleState.KILLED):
        for player_name in player_names:
            if player_name in self.roles_state:
                self.roles_state[player_name] = state

    @mark_as_readable
    def get_players_status(self, player_names: list[str]) -> dict[str, RoleState]:
        roles_state = {
            player_name: self.roles_state[player_name]
            for player_name in player_names
            if player_name in self.roles_state
        }
        return roles_state

    @mark_as_writeable
    def wolf_kill_someone(self, player_name: str):
        self.update_players_state([player_name], RoleState.KILLED)

    @mark_as_writeable
    def witch_poison_someone(self, player_name: str = None):
        self.update_players_state([player_name], RoleState.POISONED)

    @mark_as_writeable
    def witch_save_someone(self, player_name: str = None):
        self.update_players_state([player_name], RoleState.SAVED)

    @mark_as_writeable
    def update_game_states(self, memories: list):
        step_idx = self.step_idx % self.per_round_steps
        if step_idx not in [15, 18] or self.step_idx in self.eval_step_idx:
            return
        else:
            self.eval_step_idx.append(self.step_idx)  # record evaluation, avoid repetitive evaluation at the same step

        if step_idx == 15:  # step no
            # night ends: after all special roles acted, process the whole night
            self.player_current_dead = []  # reset

            if self.player_hunted != self.player_protected and not self.is_hunted_player_saved:
                self.player_current_dead.append(self.player_hunted)
            if self.player_poisoned:
                self.player_current_dead.append(self.player_poisoned)

            self.living_players = [p for p in self.living_players if p not in self.player_current_dead]
            self.update_player_status(self.player_current_dead)
            # reset
            self.player_hunted = None
            self.player_protected = None
            self.is_hunted_player_saved = False
            self.player_poisoned = None

        elif step_idx == 18:  # step no
            # day ends: after all roles voted, process all votings
            voting_msgs = memories[-len(self.living_players) :]
            voted_all = []
            for msg in voting_msgs:
                voted = re.search(r"Player[0-9]+", msg.content[-10:])
                if not voted:
                    continue
                voted_all.append(voted.group(0))
            self.player_current_dead = [Counter(voted_all).most_common()[0][0]]  # 平票时，杀最先被投的
            # print("*" * 10, "dead", self.player_current_dead)
            self.living_players = [p for p in self.living_players if p not in self.player_current_dead]
            self.update_player_status(self.player_current_dead)

        # game's termination condition
        living_werewolf = [p for p in self.werewolf_players if p in self.living_players]
        living_villagers = [p for p in self.villager_players if p in self.living_players]
        living_special_roles = [p for p in self.special_role_players if p in self.living_players]
        if not living_werewolf:
            self.winner = "good guys"
            self.win_reason = "werewolves all dead"
        elif not living_villagers or not living_special_roles:
            self.winner = "werewolf"
            self.win_reason = "villagers all dead" if not living_villagers else "special roles all dead"
        if self.winner is not None:
            self._record_all_experiences()  # TODO
