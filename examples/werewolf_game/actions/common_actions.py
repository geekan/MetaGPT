from metagpt.actions import Action

class Speak(Action):
    """Action: Any speak action in a game"""

    PROMPT_TEMPLATE = """
    ## BACKGROUND
    It's a Werewolf game, you are {profile}, say whatever possible to increase your chance of win,
    ## HISTORY
    You have knowledge to the following conversation:
    {context}
    ## YOUR TURN
    Please follow the moderator's latest instruction, FIGURE OUT if you need to speak your opinion or directly to vote,
    1. If the instruction is to speak, speak in 100 words;
    2. If the instruction is to vote, you MUST vote and ONLY say "I vote to eliminate PlayerX", where X is the player index, DO NOT include any other words.
    Your will say:
    """

    def __init__(self, name="Speak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str, profile: str):

        prompt = self.PROMPT_TEMPLATE.format(context=context, profile=profile)

        rsp = await self._aask(prompt)

        return rsp


