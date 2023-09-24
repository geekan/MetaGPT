from metagpt.actions import Action

class Protect(Action):
    """Action: choose a player to protect"""

    PROMPT_TEMPLATE = """
    It's a werewolf game and you are a guard,
    this is game history:
    {context}.
    Attention: you can not protect the same player in a row.
    Now, choose one to portect, you will:
    """

    def __init__(self, name="Speak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str):

        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)
        # rsp = "Protect Player 1"

        return rsp
