import asyncio
import collections
from random import random

from metagpt.actions import Action

STEP_INSTRUCTIONS = {
    # 上帝需要介入的全部步骤和对应指令
    # The 1-st night
    0: {"content": "It’s dark, everyone close your eyes. I will talk with you/your team secretly at night.",
        "send_to": "Moderator",  # for moderator to continuen speaking
        "restricted_to": ""},
    1: {"content": "Guard, please open your eyes!",
        "send_to": "Moderator",  # for moderator to continuen speaking
        "restricted_to": ""},
    2: {"content": """Guard, now tell me who you protect tonight? 
                You only choose one from the following living options please: {living_players}. Or you can pass. For example: I protect ...""",
        "send_to": "Guard",
        "restricted_to": "Moderator,Guard"},
    3: {"content": "Guard, close your eyes",
        "send_to": "Moderator",
        "restricted_to": ""},
    4: {"content": "Werewolves, please open your eyes!",
        "send_to": "Moderator",
        "restricted_to": ""},
    5: {"content": """Werewolves, I secretly tell you that {werewolf_players} are
                   all of the 2 werewolves! Keep in mind you are teammates. The rest players are not werewolves.
                   choose one from the following living options please:
                   {living_players}. For example: I kill ...""",
        "send_to": "Werewolf",
        "restricted_to": "Moderator,Werewolf"},
    6: {"content": "Werewolves, close your eyes",
        "send_to": "Moderator",
        "restricted_to": ""},
    7: {"content": "Witch, please open your eyes!",
        "send_to": "Moderator",
        "restricted_to": ""},
    8: {"content": """Witch, tonight {player_hunted} has been killed by the werewolves. 
                    You have a bottle of antidote, would you like to save him/her? If so, say "Save", else, say "Pass".""",
        "send_to": "Witch",
        "restricted_to": "Moderator,Witch"},  # 要先判断女巫是否有解药，再去询问女巫是否使用解药救人
    9: {"content": """Witch, you also have a bottle of poison, would you like to use it to kill one of the living players? 
                    Choose one from the following living options: {living_players}. If so, say "Poison PlayerX", where X is the player index, else, say "Pass".""",
        "send_to": "Witch",
        "restricted_to": "Moderator,Witch"},  #
    10: {"content": "Witch, close your eyes",
         "send_to": "Moderator",
         "restricted_to": ""},
    11: {"content": "Seer, please open your eyes!",
         "send_to": "Moderator",
         "restricted_to": ""},
    12: {"content": """Seer, you can check one player's identity. Who are you going to verify its identity tonight? 
                  Choose only one from the following living options:{living_players}.""",
         "send_to": "Seer",
         "restricted_to": "Moderator,Seer"},
    13: {"content": "Seer, close your eyes",
         "send_to": "Moderator",
         "restricted_to": ""},
    # The 1-st daytime
    14: {"content": """It's daytime. Everyone woke up except those who had been killed.""",
         "send_to": "Moderator",
         "restricted_to": ""},
    15: {"content": "{player_current_dead} was killed last night!",
         "send_to": "Moderator",
         "restricted_to": ""},
    16: {"content": """Now freely talk about roles of other players with each other based on your observation and 
                    reflection with few sentences. Decide whether to reveal your identity based on your reflection.""",
         "send_to": "",  # send to all to speak in daytime
         "restricted_to": ""},
    17: {"content": """Now vote and tell me who you think is the werewolf. Don’t mention your role.
                    You only choose one from the following living options please:
                    {living_players}. Or you can pass. For example: I vote to kill ...""",
         "send_to": "",
         "restricted_to": ""},
    18: {"content": """{player_current_dead} was eliminated.""",
         "send_to": "Moderator",
         "restricted_to": ""},
}

VOTE_PROMPT = """
    Welcome to the daytime discussion phase in the Werewolf game.

    During the day, players discuss and share information about who they suspect might be a werewolf.
    Players can also cast their votes to eliminate a player they believe is a werewolf.

    Here are the conversations from the daytime:

    {vote_message}

    Now it's time to cast your votes.

    You can vote for a player by typing their name.
    Example: "Vote for Player2"

    Here are the voting options:
"""

PARSE_INSTRUCTIONS = {
    0: "Now it's time to vote",
    1: "The {winner} have won! They successfully eliminated all the {loser}."
       "The game has ended. Thank you for playing Werewolf!",
    2: "The night has ended, and it's time to reveal the casualties."
       "During the night, the Werewolves made their move. Unfortunately, they targeted {PlayerName}, who is now dead."
}


class InstructSpeak(Action):
    def __init__(self, name="InstructSpeak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, step_idx, living_players, werewolf_players, player_hunted, player_current_dead):
        instruction_info = STEP_INSTRUCTIONS.get(step_idx, {
            "content": "Unknown instruction.",
            "send_to": "",
            "restricted_to": ""
        })
        content = instruction_info["content"]
        if "{living_players}" in content and "{werewolf_players}" in content:
            content = content.format(living_players=",".join(living_players),
                                     werewolf_players=",".join(werewolf_players))
        if "{living_players}" in content:
            content = content.format(living_players=",".join(living_players))
        if "{werewolf_players}" in content:
            content = content.format(werewolf_players=",".join(werewolf_players))
        if "{player_hunted}" in content:
            player_hunted = "No one" if not player_hunted else player_hunted
            content = content.format(player_hunted=player_hunted)
        if "{player_current_dead}" in content:
            content = content.format(player_current_dead=player_current_dead)

        return content, instruction_info["send_to"], instruction_info["restricted_to"]

class ParseSpeak(Action):
    def __init__(self, name="ParseSpeak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self):
        pass

class SummarizeNight(Action):
    """consider all events at night, conclude which player dies (can be a peaceful night)"""

    def __init__(self, name="SummarizeNight", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, events):
        # 假设events是一个字典，代表夜晚发生的多个事件，key是事件类型，value是该事件对应的玩家
        # 例如被狼人杀的玩家：{"killed_by_werewolves": "Player1"}
        # 被守卫守护的玩家：{"protected_by_guard": "Player2"}
        # 被女巫救的玩家：{"saved_by_witch": "Player3"}
        # 被女巫毒的玩家：{"poisoned_by_witch": "Player4"}
        # 被预言家查验的玩家：{"verified_by_seer": "Player5"}
        # 若没有事件发生，则events为空字典
        killed_by_werewolves = events.get("killed_by_werewolves", "")
        protected_by_guard = events.get("protected_by_guard", "")
        saved_by_witch = events.get("saved_by_witch", "")
        poisoned_by_witch = events.get("poisoned_by_witch", "")

        # 若狼人杀的人和守卫守的人是同一个人，那么该人就会活着；
        if protected_by_guard and killed_by_werewolves and protected_by_guard == killed_by_werewolves:
            return "It was a peaceful night. No one was killed."

        # 若守卫和女巫都救了同一个人，那么该人就会死
        if protected_by_guard and saved_by_witch and protected_by_guard == saved_by_witch:
            return f"{protected_by_guard} was killed by the werewolves."

        if saved_by_witch:
            return f"{saved_by_witch} was saved by the witch."

        if poisoned_by_witch:
            return f"{poisoned_by_witch} was poisoned by the witch."

        if killed_by_werewolves:
            return f"{killed_by_werewolves} was killed by the werewolves."


class SummarizeDay(Action):
    """consider all votes at day, conclude which player dies"""

    def __init__(self, name="SummarizeDay", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, votes):
        # 假设votes是一个字典，代表白天投票的结果，key是被投票的玩家，value是得票数
        # 例如：{"Player1": 2, "Player2": 1, "Player3": 1, "Player4": 0}
        # 表示Player1得到2票，Player2和Player3各得到1票，Player4得到0票
        # 若平票，则随机选一个人出局
        if not votes:
            return "No votes were cast. No one was killed."

        max_votes = max(votes.values())
        players_with_max_votes = [player for player, vote_count in votes.items() if vote_count == max_votes]

        if len(players_with_max_votes) == 1:
            eliminated_player = players_with_max_votes[0]
            return f"{eliminated_player} was voted out and eliminated."
        else:
            # 若平票，则随机选一个人出局
            eliminated_player = players_with_max_votes[int(random() * len(players_with_max_votes))]
            return f"There was a tie in the votes. {eliminated_player} was randomly chosen and eliminated."


class AnnounceGameResult(Action):

    async def run(self, winner: str):
        return f"Game over! The winner is the {winner}"


async def main():
    rst1 = await SummarizeDay().run({"Player1": 0, "Player2": 0, "Player3": 0, "Player4": 0})
    rst2 = await SummarizeNight().run({"killed_by_werewolves": "Player1"})
    print(rst1)
    print(rst2)

if __name__ == '__main__':
    asyncio.run(main())
