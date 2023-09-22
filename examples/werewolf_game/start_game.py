import asyncio
import platform
import fire

from examples.werewolf_game.werewolf_game import WerewolfGame
from examples.werewolf_game.roles import Moderator, Villager, Werewolf

DEFAULT_PLAYER_SETUP = """
Game setup:
Player1: Villager,
Player2: Villager,
Player3: Werewolf,
Player4: Werewolf.
"""

async def start_game(idea: str = DEFAULT_PLAYER_SETUP, investment: float = 3.0, n_round: int = 5):
    game = WerewolfGame()
    game.hire([
        Moderator(), 
        Villager(name="Player1"),
        Villager(name="Player2"),
        Werewolf(name="Player3"),
        Werewolf(name="Player4"),
    ])
    game.invest(investment)
    game.start_project(idea)
    await game.run(n_round=n_round)


def main(idea: str = DEFAULT_PLAYER_SETUP, investment: float = 3.0, n_round: int = 10):
    """
    :param idea: game config instructions
    :param investment: contribute a certain dollar amount to watch the debate
    :param n_round: maximum rounds of the debate
    :return:
    """
    asyncio.run(start_game(idea, investment, n_round))


if __name__ == '__main__':
    fire.Fire(main)
