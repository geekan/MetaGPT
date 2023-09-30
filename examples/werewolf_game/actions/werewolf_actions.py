from metagpt.actions import Action

class Hunt(Action):
    """Action: choose a villager to kill"""

    PROMPT_TEMPLATE = """
    It's a werewolf game and you are a werewolf,
    this is game history:
    {context}.
    Attention: if your previous werewolf has chosen, follow its choice.
    Format: "Kill PlayerX", where X is the player index.
    Now, choose one to kill, you will:
    """

    def __init__(self, name="Hunt", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str):

        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)
        # rsp = "Kill Player 1"

        return rsp
