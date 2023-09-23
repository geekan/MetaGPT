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
    It's daytime and it is your turn to speak, you will say (in 100 words):
    """

    def __init__(self, name="Speak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str, profile: str):

        prompt = self.PROMPT_TEMPLATE.format(context=context, profile=profile)

        rsp = await self._aask(prompt)

        return rsp


