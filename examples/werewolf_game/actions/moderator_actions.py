from metagpt.actions import Action

STAGE_INSTRUCTIONS = {
    # 上帝需要介入的全部步骤和对应指令
    # The 1-st night
    0: {"content": "It’s dark, everyone close your eyes. I will talk with you/your team secretly at night.",
        "send_to": "Moderator", # for moderator to continuen speaking
        "restricted_to": ""},
    1: {"content": "Werewolves, please open your eyes!",
        "send_to": "Moderator", # for moderator to continuen speaking
        "restricted_to": ""},
    2: {"content": """Werewolves, I secretly tell you that Player 3 and Player 4 are
                   all of the 2 werewolves! Keep in mind you are teammates. The rest players are not werewolves.
                   choose one from the following living options please:
                   [Player 1, Player2]. """, # send to werewolf restrictedly for a response
        "send_to": "Werewolf",
        "restricted_to": "Werewolf"},
    3: {"content": "Werewolves, close your eyes",
        "send_to": "Moderator", # for moderator to continuen speaking
        "restricted_to": ""},
    4: {"content": """It's daytime. No one dies last night. Now freely talk about roles of other players with each other based on your observation and reflection
                   with few sentences. Decide whether to reveal your identity based on your reflection.""",
        "send_to": "", # send to all to speak in daytime
        "restricted_to": ""}
}

class InstructSpeak(Action):
    def __init__(self, name="InstructSpeak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, stage_idx):
        return STAGE_INSTRUCTIONS[stage_idx]

class ParseSpeak(Action):
    async def run(self):
        return ""

class SummarizeNight(Action):
    """consider all events at night, conclude which player dies (can be a peaceful night)"""
    pass

class SummarizeDay(Action):
    """consider all votes at day, conclude which player dies"""
    pass

class AnnounceGameResult(Action):

    async def run(self, winner: str):
        return f"Game over! The winner is {winner}"
