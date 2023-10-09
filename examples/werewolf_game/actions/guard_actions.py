from metagpt.actions import Action
from examples.werewolf_game.actions import NighttimeWhispers

class Protect(NighttimeWhispers):

    def __init__(self, name="Protect", context=None, llm=None):
        super().__init__(name, context, llm)
