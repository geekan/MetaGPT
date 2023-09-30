from metagpt.actions import Action

class Save(Action):
    """Action: choose a villager to Save"""

    PROMPT_TEMPLATE = """
    It's a werewolf game and you are a witch,
    this is game history:
    {context}.
    Follow the Moderator's instruction, decide whether you want to save that person or not:
    """

    def __init__(self, name="Save", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str):

        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)
        # rsp = "Save Player 1"

        return rsp

class Poison(Action):
    """Action: choose a villager to Poison"""

    PROMPT_TEMPLATE = """
    It's a werewolf game and you are a witch,
    this is game history:
    {context}.
    Follow the Moderator's instruction, decide whether you want to poison another person or not:
    """

    def __init__(self, name="Poison", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str):

        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)
        # rsp = "Poison Player 1"

        return rsp
