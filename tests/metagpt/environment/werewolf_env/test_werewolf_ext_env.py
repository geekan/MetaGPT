#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of WerewolfExtEnv


from metagpt.environment.werewolf_env.werewolf_ext_env import RoleState, WerewolfExtEnv


def test_werewolf_ext_env():
    ext_env = WerewolfExtEnv()

    game_setup = """Game setup:
    Player0: Werewolf,
    Player1: Werewolf,
    Player2: Villager,
    Player3: Guard,
    """
    ext_env.parse_game_setup(game_setup)
    assert len(ext_env.living_players) == 4
    assert len(ext_env.special_role_players) == 1
    assert len(ext_env.werewolf_players) == 2

    curr_instr = ext_env.curr_step_instruction()
    assert ext_env.step_idx == 1
    assert "close your eyes" in curr_instr["content"]

    player_names = ["Player0", "Player2"]
    ext_env.update_players_state(player_names, RoleState.KILLED)
    assert ext_env.get_players_status(player_names) == dict(zip(player_names, [RoleState.KILLED] * 2))
