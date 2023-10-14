from metagpt.actions import Action
from examples.werewolf_game.actions import NighttimeWhispers

class Save(NighttimeWhispers):
    def __init__(self, name="Save", context=None, llm=None):
        super().__init__(name, context, llm)

    def _update_prompt_json(
        self, prompt_json: dict, role_profile: str, role_name: str, context: str, reflection: str, experiences: str
    ) -> dict:
        del prompt_json['ACTION']
        del prompt_json['ATTENTION']

        prompt_json["OUTPUT_FORMAT"]["THOUGHTS"] = "It is night time. Return the thinking steps of your decision of whether to save the player JUST killed this night."
        prompt_json["OUTPUT_FORMAT"]["RESPONSE"] = "Follow the Moderator's instruction, decide whether you want to save that person or not. Return SAVE or PASS."

        return prompt_json
    
    async def run(self, *args, **kwargs):
        rsp = await super().run(*args, **kwargs)
        action_name, rsp = rsp.split()
        return rsp # 只需回复SAVE或PASS，不需要带上action名

class Poison(NighttimeWhispers):
    STRATEGY = """
    Only poison a player if you are confident he/she is a werewolf. Don't poison a player randomly or at first night.
    If someone claims to be the witch, poison him/her, because you are the only witch, he/she can only be a werewolf.
    """

    def __init__(self, name="Poison", context=None, llm=None):
        super().__init__(name, context, llm)

    def _update_prompt_json(
        self, prompt_json: dict, role_profile: str, role_name: str, context: str, reflection: str, experiences: str
    ) -> dict:
        prompt_json["OUTPUT_FORMAT"]["RESPONSE"] += "Or if you want to PASS, return PASS."
        return prompt_json

    async def run(self, *args, **kwargs):
        rsp = await super().run(*args, **kwargs)
        if "pass" in rsp.lower():
            action_name, rsp = rsp.split() # 带PASS，只需回复PASS，不需要带上action名，否则是Poison PlayerX，无需改动
        return rsp
