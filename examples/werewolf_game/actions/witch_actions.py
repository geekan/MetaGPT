from metagpt.actions import Action
from examples.werewolf_game.actions import NighttimeWhispers

class Save(NighttimeWhispers):
    def __init__(self, name="Save", context=None, llm=None):
        super().__init__(name, context, llm)

    def _update_prompt_json(self, prompt_json: dict, profile: str, name: str, context: str, **kwargs):
        del prompt_json['ACTION']
        del prompt_json['ATTENTION']

        prompt_json["OUTPUT_FORMAT"]["THOUGHTS"] = "It is night time. Return the thinking steps of your decision of whether to save the player JUST be killed at this night."
        prompt_json["OUTPUT_FORMAT"]["RESPONSE"] = "Follow the Moderator's instruction, decide whether you want to save that person or not. Return SAVE or PASS."

        return prompt_json

class Poison(NighttimeWhispers):
    STRATEGY = """
    Only poison a player if you are confident he/she is a werewolf. Don't poison a player randomly or at first night.
    If someone claims to be the witch, poison him/her, because you are the only witch, he/she can only be a werewolf.
    """

    def __init__(self, name="Poison", context=None, llm=None):
        super().__init__(name, context, llm)

    def _update_prompt_json(self, prompt_json: dict, profile: str, name: str, context: str, **kwargs):

        prompt_json["OUTPUT_FORMAT"]["RESPONSE"] += "Or if you want to PASS, return PASS."

        return prompt_json
