import asyncio
import platform
import fire
import random

from metagpt.logs import logger
from examples.werewolf_game.werewolf_game import WerewolfGame
from examples.werewolf_game.roles import Moderator, Villager, Werewolf, Guard, Seer, Witch
from examples.werewolf_game.roles.human_player import prepare_human_player

def init_game_setup(shuffle=True, add_human=False):
    roles = [
        Villager,
        Villager,
        Werewolf
    ]
    if shuffle:
        # random.seed(2023)
        random.shuffle(roles)
    if add_human:
        assigned_role_idx = random.randint(0, len(roles) - 1)
        assigned_role = roles[assigned_role_idx]
        roles[assigned_role_idx] = prepare_human_player(assigned_role)

    players = [role(name=f"Player{i+1}") for i, role in enumerate(roles)]

    if add_human:
        logger.info(f"You are assigned {players[assigned_role_idx].name}({players[assigned_role_idx].profile})")

    game_setup = ["Game setup:"] + [f"{player.name}: {player.profile}," for player in players]
    begin_prompt = "Game begins!"
    game_setup = "\n".join(game_setup) + "\n" + begin_prompt

    return game_setup, players

async def start_game(investment: float = 3.0, n_round: int = 5, shuffle : bool = True, add_human: bool = False):
    game = WerewolfGame()
    game_setup, players = init_game_setup(shuffle=shuffle, add_human=add_human)
    players = [Moderator()] + players
    game.hire(players)
    game.invest(investment)
    game.start_project(game_setup)
    await game.run(n_round=n_round)

def main(investment: float = 3.0, n_round: int = 100, shuffle : bool = True, add_human: bool = False):
    """
    :param investment: contribute a certain dollar amount to watch the debate
    :param n_round: maximum rounds of the debate
    :return:
    """
    asyncio.run(start_game(investment, n_round, shuffle, add_human))


if __name__ == '__main__':
    fire.Fire(main)
