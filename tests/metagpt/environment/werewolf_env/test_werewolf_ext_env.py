#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of WerewolfExtEnv

from metagpt.environment.werewolf.const import RoleState, RoleType
from metagpt.environment.werewolf.werewolf_ext_env import WerewolfExtEnv
from metagpt.roles.role import Role


class Werewolf(Role):
    profile: str = RoleType.WEREWOLF.value


class Villager(Role):
    profile: str = RoleType.VILLAGER.value


class Witch(Role):
    profile: str = RoleType.WITCH.value


class Guard(Role):
    profile: str = RoleType.GUARD.value


def test_werewolf_ext_env():
    players_state = {
        "Player0": (RoleType.WEREWOLF.value, RoleState.ALIVE),
        "Player1": (RoleType.WEREWOLF.value, RoleState.ALIVE),
        "Player2": (RoleType.VILLAGER.value, RoleState.ALIVE),
        "Player3": (RoleType.WITCH.value, RoleState.ALIVE),
        "Player4": (RoleType.GUARD.value, RoleState.ALIVE),
    }
    ext_env = WerewolfExtEnv(players_state=players_state, step_idx=4, special_role_players=["Player3", "Player4"])

    assert len(ext_env.living_players) == 5
    assert len(ext_env.special_role_players) == 2
    assert len(ext_env.werewolf_players) == 2

    curr_instr = ext_env.curr_step_instruction()
    assert ext_env.step_idx == 5
    assert "Werewolves, please open your eyes" in curr_instr["content"]

    # current step_idx = 5
    ext_env.wolf_kill_someone(wolf_name="Player10", player_name="Player4")
    ext_env.wolf_kill_someone(wolf_name="Player0", player_name="Player4")
    ext_env.wolf_kill_someone(wolf_name="Player1", player_name="Player4")
    assert ext_env.player_hunted == "Player4"
    assert len(ext_env.living_players) == 5  # hunted but can be saved by witch

    for idx in range(13):
        _ = ext_env.curr_step_instruction()

    # current step_idx = 18
    assert ext_env.step_idx == 18
    ext_env.vote_kill_someone(voter_name="Player0", player_name="Player2")
    ext_env.vote_kill_someone(voter_name="Player1", player_name="Player3")
    ext_env.vote_kill_someone(voter_name="Player2", player_name="Player3")
    ext_env.vote_kill_someone(voter_name="Player3", player_name="Player4")
    ext_env.vote_kill_someone(voter_name="Player4", player_name="Player2")
    assert ext_env.player_current_dead == "Player2"
    assert len(ext_env.living_players) == 4

    player_names = ["Player0", "Player2"]
    assert ext_env.get_players_state(player_names) == dict(zip(player_names, [RoleState.ALIVE, RoleState.KILLED]))
