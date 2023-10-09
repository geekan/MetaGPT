from metagpt.actions import Action
from examples.werewolf_game.actions import NighttimeWhispers

class Verify(NighttimeWhispers):
    def __init__(self, name="Verify", context=None, llm=None):
        super().__init__(name, context, llm)
