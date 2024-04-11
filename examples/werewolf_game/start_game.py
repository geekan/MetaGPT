import asyncio

import fire

from metagpt.ext.werewolf.roles import Guard, Moderator, Seer, Villager, Werewolf, Witch
from metagpt.ext.werewolf.roles.human_player import prepare_human_player
from metagpt.ext.werewolf.werewolf_game import WerewolfGame
from metagpt.logs import logger


async def start_game(
    investment: float = 3.0,
    n_round: int = 5,
    shuffle: bool = True,
    add_human: bool = False,
    use_reflection: bool = True,
    use_experience: bool = False,
    use_memory_selection: bool = False,
    new_experience_version: str = "",
):
    game = WerewolfGame()
    game_setup, players = game.env.init_game_setup(
        role_uniq_objs=[Villager, Werewolf, Guard, Seer, Witch],
        num_werewolf=2,
        num_villager=2,
        shuffle=shuffle,
        add_human=add_human,
        use_reflection=use_reflection,
        use_experience=use_experience,
        use_memory_selection=use_memory_selection,
        new_experience_version=new_experience_version,
        prepare_human_player=prepare_human_player,
    )
    logger.info(f"{game_setup}")

    players = [Moderator()] + players
    game.hire(players)
    game.invest(investment)
    game.run_project(game_setup)
    await game.run(n_round=n_round)


def main(
    investment: float = 20.0,
    n_round: int = 100,
    shuffle: bool = True,
    add_human: bool = False,
    use_reflection: bool = True,
    use_experience: bool = False,
    use_memory_selection: bool = False,
    new_experience_version: str = "",
):
    asyncio.run(
        start_game(
            investment,
            n_round,
            shuffle,
            add_human,
            use_reflection,
            use_experience,
            use_memory_selection,
            new_experience_version,
        )
    )


if __name__ == "__main__":
    fire.Fire(main)
