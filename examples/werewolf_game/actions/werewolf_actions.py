from metagpt.actions import Action
from examples.werewolf_game.actions.common_actions import Speak

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

class Impersonate(Speak):
    """Action: werewolf impersonating a good guy in daytime speak"""

    PROMPT_TEMPLATE = """
    ## BACKGROUND
    It's a Werewolf game, you are {profile}, say whatever possible to increase your chance of win,
    ## HISTORY
    You have knowledge to the following conversation:
    {context}
    ## ATTENTION: Try continuously impersonating a role with special ability, such as a Seer or a Witch, in order to mislead
    other players, make them trust you, and thus hiding your werewolf identity
    ## YOUR TURN
    Please follow the moderator's latest instruction, FIGURE OUT if you need to speak your opinion or directly to vote,
    1. If the instruction is to speak, speak in 100 words;
    2. If the instruction is to vote, you MUST vote and ONLY say "I vote to eliminate PlayerX", where X is the player index, DO NOT include any other words.
    Your will say:
    """

    def __init__(self, name="Impersonate", context=None, llm=None):
        super().__init__(name, context, llm)
