#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : The werewolf game external environment to integrate with

import random
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

    players_state: dict[str, tuple[str, RoleState]] = Field(
        default=dict(), description="the player's role type and state by player_name"
    )

    round_idx: int = Field(default=0)  # the current round
    step_idx: int = Field(default=0)  # the current step of current round
    eval_step_idx: int = Field(default=0)
    per_round_steps: int = Field(default=len(STEP_INSTRUCTIONS))

    # game global states
    game_setup: str = Field(default="", description="game setup including role and its num")
    special_role_players: list[str] = Field(default=[])
    winner: Optional[str] = Field(default=None)
    win_reason: Optional[str] = Field(default=None)
    witch_poison_left: int = Field(default=1)
    witch_antidote_left: int = Field(default=1)

    # game current round states, a round is from closing your eyes to the next time you close your eyes
    round_hunts: dict[str, str] = Field(default=dict(), description="nighttime wolf hunt result")
    round_votes: dict[str, str] = Field(
        default=dict(), description="daytime all players vote result, key=voteer, value=voted one"
    )
    player_hunted: Optional[str] = Field(default=None)
    player_protected: Optional[str] = Field(default=None)
    is_hunted_player_saved: bool = Field(default=False)
    player_poisoned: Optional[str] = Field(default=None)
    player_current_dead: list[str] = Field(default=[])

    @property
    def living_players(self) -> list[str]:
        player_names = []
        for name, roletype_state in self.players_state.items():
            if roletype_state[1] in [RoleState.ALIVE, RoleState.SAVED]:
                player_names.append(name)
        return player_names

    def _role_type_players(self, role_type: str) -> list[str]:
        """return player name of particular role type"""
        player_names = []
        for name, roletype_state in self.players_state.items():
            if role_type in roletype_state[0]:
                player_names.append(name)
        return player_names

    @property
    def werewolf_players(self) -> list[str]:
        player_names = self._role_type_players(role_type="Werewolf")
        return player_names

    @property
    def villager_players(self) -> list[str]:
        player_names = self._role_type_players(role_type="Villager")
        return player_names

    def _init_players_state(self, players: list["Role"]):
        for play in players:
            self.players_state[play.name] = (play.profile, RoleState.ALIVE)

        self.special_role_players = [
            p for p in self.living_players if p not in self.werewolf_players + self.villager_players
        ]

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
        """init players using different roles' num"""
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
        self.game_setup = "\n".join(game_setup)

        self._init_players_state(players)  # init players state

        return self.game_setup, players

    def _update_players_state(self, player_names: list[str], state: RoleState = RoleState.KILLED):
        for player_name in player_names:
            if player_name in self.players_state:
                roletype_state = self.players_state[player_name]
                self.players_state[player_name] = (roletype_state[0], state)

    def _check_valid_role(self, player: "Role", role_type: str) -> bool:
        return True if role_type in str(player) else False

    def _check_player_continue(self, player_name: str, particular_step: int = -1) -> bool:
        step_idx = self.step_idx % self.per_round_steps
        if particular_step > 0 and step_idx != particular_step:  # step no
            # particular_step = 18, not daytime vote time, ignore
            # particular_step = 15, not nighttime hunt time, ignore
            return False
        if player_name not in self.living_players:
            return False
        return True

    @mark_as_readable
    def curr_step_instruction(self) -> dict:
        step_idx = self.step_idx % len(STEP_INSTRUCTIONS)
        instruction = STEP_INSTRUCTIONS[step_idx]
        self.step_idx += 1
        return instruction

    @mark_as_readable
    def get_players_state(self, player_names: list[str]) -> dict[str, RoleState]:
        players_state = {
            player_name: self.players_state[player_name][1]  # only return role state
            for player_name in player_names
            if player_name in self.players_state
        }
        return players_state

    @mark_as_writeable
    def vote_kill_someone(self, voteer: "Role", player_name: str = None):
        """player vote result at daytime
        player_name: if it's None, regard as abstaining from voting
        """
        if not self._check_player_continue(voteer.name, particular_step=18):  # 18=step no
            return

        self.round_votes[voteer.name] = player_name
        # check if all living players finish voting, then get the dead one
        if list(self.round_votes.keys()) == self.living_players:
            voted_all = list(self.round_votes.values())  # TODO in case of tie vote, check who was voted first
            voted_all = [item for item in voted_all if item]
            self.player_current_dead = Counter(voted_all).most_common()[0][0]
            self._update_players_state([self.player_current_dead])

    @mark_as_writeable
    def wolf_kill_someone(self, wolf: "Role", player_name: str):
        if not self._check_valid_role(wolf, "Werewolf"):
            return
        if not self._check_player_continue(wolf.name, particular_step=5):  # 5=step no
            return

        self.round_hunts[wolf.name] = player_name
        living_werewolf = [p for p in self.werewolf_players if p in self.living_players]
        # check if all living wolfs finish hunting, then get the hunted one
        if list(self.round_hunts.keys()) == living_werewolf:
            hunted_all = list(self.round_hunts.values())
            self.player_hunted = Counter(hunted_all).most_common()[0][0]

    @mark_as_writeable
    def witch_poison_someone(self, witch: "Role", player_name: str = None):
        if not self._check_valid_role(witch, "Witch"):
            return
        if not self._check_player_continue(player_name):
            return

        self._update_players_state([player_name], RoleState.POISONED)
        self.player_poisoned = player_name

    @mark_as_writeable
    def witch_save_someone(self, witch: "Role", player_name: str = None):
        if not self._check_valid_role(witch, "Witch"):
            return
        if not self._check_player_continue(player_name):
            return

        self._update_players_state([player_name], RoleState.SAVED)
        self.player_protected = player_name

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

            self._update_players_state([self.player_current_dead])
            # reset
            self.player_hunted = None
            self.player_protected = None
            self.is_hunted_player_saved = False
            self.player_poisoned = None

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
