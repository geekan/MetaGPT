from metagpt.actions import Action


class Verify(Action):
    """Action: Seer verifies a player's identity at night"""

    PROMPT_TEMPLATE = """
    It's a werewolf game and you are a seer.
    You can choose to verify the identity of a player.
    Here's the game history:
    {context}.
    Now, choose one player to verify:
    """

    def __init__(self, name="Verify", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)

        return rsp
