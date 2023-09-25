from metagpt.actions import Action

STAGE_INSTRUCTIONS = {
    # 上帝需要介入的全部步骤和对应指令
    # The 1-st night
    0: {"content": "It’s dark, everyone close your eyes. I will talk with you/your team secretly at night.",
        "send_to": "Moderator",  # for moderator to continuen speaking
        "restricted_to": ""},
    1: {"content": "Guard, please open your eyes!",
        "send_to": "Moderator",  # for moderator to continuen speaking
        "restricted_to": ""},
    2: {"content": """Guard, now tell me who you protect tonight? 
                You only choose one from the following living options please: {living_players}.""",
        "send_to": "Guard",
        "restricted_to": "Guard"},
    3: {"content": "Guard, close your eyes",
        "send_to": "Moderator",
        "restricted_to": ""},
    4: {"content": "Werewolves, please open your eyes!",
        "send_to": "Moderator",
        "restricted_to": ""},
    5: {"content": """Werewolves, I secretly tell you that xxx and xxx are
                   all of the 2 werewolves! Keep in mind you are teammates. The rest players are not werewolves.
                   choose one from the following living options please:
                   {living_players}. """,  # send to werewolf restrictedly for a response
        "send_to": "Werewolf",
        "restricted_to": "Werewolf"},
    6: {"content": "Werewolves, close your eyes",
        "send_to": "Moderator",
        "restricted_to": ""},
    7: {"content": "Seer, please open your eyes!",
        "send_to": "Moderator",
        "restricted_to": ""},
    8: {"content": """Seer, you can check one player's identity. Who are you going to verify its identity tonight? 
                      Choose only one from the following living options:{living_players}.""",
        "send_to": "Seer",
        "restricted_to": "Seer"},
    9: {"content": "Seer, close your eyes",
        "send_to": "Moderator",
        "restricted_to": ""},
    10: {"content": "Witch, please open your eyes!",
         "send_to": "Moderator",
         "restricted_to": ""},
    11: {"content": """Witch, you have a bottle of poison, who are you going to kill tonight?
                        Choose one from the following living options: {living_players}.""",
         "send_to": "Witch",
         "restricted_to": "Witch"},
    12: {"content": """Witch, you have a bottle of antidote and a bottle of poison. 
                        Who are you going to save tonight or kill tonight? Choose one from the following living options: 
                        {living_players}.""",
         "send_to": "Witch",
         "restricted_to": "Witch"},
    13: {"content": "Witch, close your eyes",
         "send_to": "Moderator",
         "restricted_to": ""},
    # The 1-st daytime
    14: {"content": """It's daytime. Everyone woke up except those who had been killed.""",
         "send_to": "Moderator",
         "restricted_to": ""},
    15: {"content": "xxxx was killed last night. Or, it was a peaceful night and no one died!",
         "send_to": "Moderator",
         "restricted_to": ""},
    16: {"content": """Now freely talk about roles of other players with each other based on your observation and 
                    reflection with few sentences. Decide whether to reveal your identity based on your reflection.""",
         "send_to": "",  # send to all to speak in daytime
         "restricted_to": ""},
    17: {"content": """Now vote and tell me who you think is the werewolf. Don’t mention your role.
                    You only choose one from the following living options please:
                    {living_players}. Or you can pass. For example: I vote to kill xxxx""",
         "send_to": "Moderator",
         "restricted_to": ""},
    18: {"content": """xxxx was eliminated.""",
         "send_to": "Moderator",
         "restricted_to": ""},
}

INSTRUCT_SPEAK_TEMPLATE = """
## BACKGROUND
It's a Werewolf game, you are moderator.

## STAGE
The current stage of the game is: 
{}

## CONTEXT
Here's the current context:
{}

What would you like to instruct?
"""
class InstructSpeak(Action):
    def __init__(self, name="InstructSpeak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context,living_players, stage_idx):

        instruction_info = STAGE_INSTRUCTIONS.get(stage_idx, "Unknown instruction.")
        # 利用上下文信息context和所处阶段的信息
        if "{living_players}" in instruction_info["content"]:
            content = instruction_info["content"].format(living_players)
        else:
            content = instruction_info["content"]

        prompt = INSTRUCT_SPEAK_TEMPLATE.format(content, context)

        rsp = await self._aask(prompt)

        send_to = instruction_info["send_to"]
        restricted_to = instruction_info["restricted_to"]

        return rsp, send_to, restricted_to


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
