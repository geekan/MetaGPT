import asyncio
import platform
import fire
import random

from examples.werewolf_game.werewolf_game import WerewolfGame
from examples.werewolf_game.roles import Moderator, Villager, Werewolf, Guard, Seer, Witch

def init_game_setup(shuffle=False):
    roles = [
        Villager,
        Villager,
        Werewolf,
        Werewolf,
        Guard,
        Seer,
        Witch
    ]
    if shuffle:
        random.seed(2023)
        random.shuffle(roles)
    players = [role(name=f"Player{i+1}") for i, role in enumerate(roles)]
    game_setup = ["Game setup:"] + [f"{player.name}: {player.profile}," for player in players]
    game_setup = "\n".join(game_setup)
    return game_setup, players

async def start_game(investment: float = 3.0, n_round: int = 5):
    game = WerewolfGame()
    game_setup, players = init_game_setup(shuffle=True)
    players = [Moderator()] + players
    game.hire(players)
    game.invest(investment)
    game.start_project(game_setup)
    await game.run(n_round=n_round)

def main(investment: float = 3.0, n_round: int = 100):
    """
    :param investment: contribute a certain dollar amount to watch the debate
    :param n_round: maximum rounds of the debate
    :return:
    """
    asyncio.run(start_game(investment, n_round))


if __name__ == '__main__':
    fire.Fire(main)
