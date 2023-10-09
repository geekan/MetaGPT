from metagpt.actions import Action
import json
from metagpt.const import WORKSPACE_ROOT


class Speak(Action):
    """Action: Any speak action in a game"""

    PROMPT_TEMPLATE = """
    {
    "BACKGROUND": "It's a Werewolf game, you are __profile__, say whatever possible to increase your chance of win"
    ,"HISTORY": "You have knowledge to the following conversation: __context__"
    ,"ATTENTION": "You can NOT VOTE a player who is NOT ALIVE now!"
    ,"STRATEGY": __strategy__
    ,"MODERATOR_INSTRUCTION": __latest_instruction__,
    ,"RULE": "Please follow the moderator's latest instruction, figure out if you need to speak your opinion or directly to vote:
              1. If the instruction is to SPEAK, speak in 200 words. Remember the goal of your role and try to achieve it using your speech;
              2. If the instruction is to VOTE, you MUST vote and ONLY say 'I vote to eliminate PlayerX', replace PlayerX with the actual player name, DO NOT include any other words."
    ,"OUTPUT_FORMAT":
        {
        "ROLE": "Your role, in this case, __profile__"
        ,"PLAYER_NAME": "Your name, in this case, __name__"
        ,"LIVING_PLAYERS": "List living players based on MODERATOR_INSTRUCTION. Return a LIST datatype."
        ,"THOUGHTS": "Based on `MODERATOR_INSTRUCTION` and `RULE`, carefully think about what to say or vote so that your chance of win as __profile__ maximizes. Give your step-by-step thought process, you should think no more than 3 steps. For example: My step-by-step thought process:..."
        ,"RESPONSE": "Based on `MODERATOR_INSTRUCTION`, `RULE`, and the 'THOUGHTS' you had, express your opinion or cast a vote."
        }
    }
    """
    STRATEGY = """
    Decide whether to reveal your identity based on benefits vs. risks, provide useful information, and vote to eliminate the most suspicious.
    If you have special abilities, pay attention to those who falsely claims your role, for they are probably werewolves.
    """

    def __init__(self, name="Speak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, profile: str, name: str, context: str, latest_instruction: str):

        prompt = (
            self.PROMPT_TEMPLATE.replace("__context__", context).replace("__profile__", profile)
            .replace("__name__", name).replace("__latest_instruction__", latest_instruction)
            .replace("__strategy__", self.STRATEGY)
        )

        re_run = 2
        while re_run > 0:
            rsp = await self._aask(prompt)
            try:
                rsp = rsp.replace("\n", " ")
                rsp_json = json.loads(rsp)
                break
            except:
                re_run -= 1

        with open(WORKSPACE_ROOT / 'speak.txt', 'a') as f:
            f.write(rsp)

        return rsp_json['RESPONSE']

class NighttimeWhispers(Action):
    """

    Action: nighttime whispers with thinking processes

    Usage Example:

        class Hunt(NighttimeWhispers):
            def __init__(self, name="Hunt", context=None, llm=None):
                super().__init__(name, context, llm)

        class Protect(NighttimeWhispers):
            def __init__(self, name="Protect", context=None, llm=None):
                super().__init__(name, context, llm)

        class Verify(NighttimeWhispers):
            def __init__(self, name="Verify", context=None, llm=None):
                super().__init__(name, context, llm)

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
            def __init__(self, name="Poison", context=None, llm=None):
                super().__init__(name, context, llm)

            def _update_prompt_json(self, prompt_json: dict, profile: str, name: str, context: str, **kwargs):
                prompt_json["OUTPUT_FORMAT"]["RESPONSE"] += "Or if you want to PASS, return PASS."
                return prompt_json
    """

    PROMPT_TEMPLATE = """
    {
    "ROLE": "__profile__"
    ,"ACTION": "Choose one living player to __action__."
    ,"ATTENTION": "1. You can only __action__ a player who is alive this night! And you can not __action__ a player who is dead this night!  2. `HISTORY` is all the information you observed, DONT hallucinate other player actions!"
    ,"STRATEGY": "__strategy__"
    ,"BACKGROUND": "It's a werewolf game and you are a __profile__. Here's the game history: __context__."
    ,"OUTPUT_FORMAT":
        {
        "ROLE": "Your role, in this case, __profile__"
        ,"PLAYER_NAME": "Your name, in this case, __name__"
        ,"LIVING_PLAYERS": "List the players who is alive based on moderator's latest instruction. Return a LIST datatype."
        ,"THOUGHTS": "Choose one living player from `LIVING_PLAYERS` to __action__ this night. Return the reason why you choose to __action__ this player. If you observe nothing at first night, DONT imagine unexisting player actions! Give your step-by-step thought process, you should think no more than 3 steps. For example: My step-by-step thought process:..."
        ,"RESPONSE": "As a __profile__, you should choose one living player from `LIVING_PLAYERS` to __action__ this night according to the THOUGHTS you have just now. Return the player name ONLY."
        }
    }
    """
    STRATEGY = """
    Decide which player is most threatening to you or most needs your support, take your action correspondingly.
    """

    def __init__(self, name="NightTimeWhispers", context=None, llm=None):
        super().__init__(name, context, llm)

    def _construct_prompt_json(self, role_profile: str, role_name: str, context: str, **kwargs):
        prompt_template = self.PROMPT_TEMPLATE

        def replace_string(prompt_json: dict):
            k: str
            for k in prompt_json.keys():
                if isinstance(prompt_json[k], dict):
                    prompt_json[k] = replace_string(prompt_json[k])
                    continue
                prompt_json[k] = prompt_json[k].replace("__profile__", role_profile)
                prompt_json[k] = prompt_json[k].replace("__name__", role_name)
                prompt_json[k] = prompt_json[k].replace("__context__", context)
                prompt_json[k] = prompt_json[k].replace("__action__", self.name)
                prompt_json[k] = prompt_json[k].replace("__strategy__", self.STRATEGY)

            return prompt_json
        
        prompt_json: dict = json.loads(prompt_template)

        prompt_json = replace_string(prompt_json)

        prompt_json: dict = self._update_prompt_json(prompt_json, role_profile, role_name, context, **kwargs)
        assert isinstance(prompt_json, dict)

        prompt: str = json.dumps(prompt_json, indent=4, separators=(',', ': '), ensure_ascii=False)
        
        return prompt

    def _update_prompt_json(self, prompt_json: dict, role_profile: str, role_name: str, context: str) -> dict:
        # one can modify the prompt_json dictionary here
        return prompt_json

    async def run(self, context: str, profile: str, name: str):

        final_prompt = self._construct_prompt_json(
            role_profile=profile, role_name=name, context=context
        )

        re_run = 2
        while re_run > 0:
            rsp_content = await self._aask(final_prompt)
            try:
                rsp_content = rsp_content.replace("\n", " ")
                rsp = json.loads(rsp_content)
                break
            except:
                re_run -= 1

        with open(WORKSPACE_ROOT / f'{self.name}.txt', 'a') as f:
            f.write(rsp_content)

        return f"{self.name} " + str(rsp["RESPONSE"])
