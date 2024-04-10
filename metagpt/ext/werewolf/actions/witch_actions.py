from metagpt.environment.werewolf.const import RoleActionRes
from metagpt.ext.werewolf.actions.common_actions import NighttimeWhispers


class Save(NighttimeWhispers):
    name: str = "Save"

    def _update_prompt_json(
        self, prompt_json: dict, role_profile: str, role_name: str, context: str, reflection: str, experiences: str
    ) -> dict:
        del prompt_json["ACTION"]
        del prompt_json["ATTENTION"]

        prompt_json["OUTPUT_FORMAT"][
            "THOUGHTS"
        ] = "It is night time. Return the thinking steps of your decision of whether to save the player JUST killed this night."
        prompt_json["OUTPUT_FORMAT"][
            "RESPONSE"
        ] = "Follow the Moderator's instruction, decide whether you want to save that person or not. Return SAVE or PASS."

        return prompt_json

    async def run(self, *args, **kwargs):
        rsp = await super().run(*args, **kwargs)
        action_name, rsp = rsp.split()
        return rsp  # 只需回复SAVE或PASS，不需要带上action名


class Poison(NighttimeWhispers):
    STRATEGY: str = """
    Only poison a player if you are confident he/she is a werewolf. Don't poison a player randomly or at first night.
    If someone claims to be the witch, poison him/her, because you are the only witch, he/she can only be a werewolf.
    """

    name: str = "Poison"

    def _update_prompt_json(
        self, prompt_json: dict, role_profile: str, role_name: str, context: str, reflection: str, experiences: str
    ) -> dict:
        prompt_json["OUTPUT_FORMAT"]["RESPONSE"] += "Or if you want to PASS, return PASS."
        return prompt_json

    async def run(self, *args, **kwargs):
        rsp = await super().run(*args, **kwargs)
        if RoleActionRes.PASS.value in rsp.lower():
            action_name, rsp = rsp.split()  # 带PASS，只需回复PASS，不需要带上action名，否则是Poison PlayerX，无需改动
        return rsp
