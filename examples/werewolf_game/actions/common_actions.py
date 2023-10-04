from metagpt.actions import Action
import json
from metagpt.const import WORKSPACE_ROOT


class Speak(Action):
    """Action: Any speak action in a game"""

    PROMPT_TEMPLATE = """
    {
    "BACKGROUND": "It's a Werewolf game, you are __profile__, say whatever possible to increase your chance of win"
    ,"HISTORY": "You have knowledge to the following conversation: __context__"
    ,"ATTENTION": "You can not VOTE a player who is NOT ALIVE now! And be careful of revealing your identity !"
    ,"YOUR_TURN": "Please follow the moderator's latest instruction, FIGURE OUT if you need to speak your opinion or directly to vote,
                1. If the instruction is to SPEAK, speak in 200 words. Remember the goal of your role and try to achieve it using your speech;
                2. If the instruction is to VOTE, you MUST vote and ONLY say 'I vote to eliminate PlayerX', where X is the player index. 
                DO NOT include any other words.
                "
    ,"OUTPUT_FORMAT":
        {
        "ROLE": "Your role."
        ,"NUMBER": "Your player number."
        ,"IDENTITY": "You are? What is you identity? You are player1 or player2 or player3 or player4 or player5 or player6 or player7?"
        ,"LIVING_PLAYERS": "List the players who is alive. Return a LIST datatype."
        ,"THOUGHTS": "It is day time. Return the thinking steps of your decision of giving VOTE to other player from `LIVING_PLAYERS`. And return the reason why you choose to VOTE this player from `LIVING_PLAYERS`."
        ,"SPEECH_OR_VOTE": "Follow the instruction of `YOUR_TURN` above and the `THOUGHTS` you have just now, give a speech or your vote."
        }

    }
    """

    def __init__(self, name="Speak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str, profile: str):

        # prompt = self.PROMPT_TEMPLATE.format(context=context, profile=profile)
        prompt = self.PROMPT_TEMPLATE.replace("__context__", context).replace("__profile__", profile)

        rsp = await self._aask(prompt)
        re_run = 2
        while re_run > 0:
            try:
                rsp_json = json.loads(rsp)
                break
            except:
                re_run -= 1

        with open(WORKSPACE_ROOT / 'speak.txt', 'a') as f:
            f.write(rsp)

        return rsp_json['SPEECH_OR_VOTE']

class NighttimeWhispers(Action):
    """

    Action: nighttime whispers with thinking processes

    Usage Example:

        class Hunt(NighttimeWhispers):
            ROLE = "Werewolf"
            ACTION = "KILL"
            IF_RENEW = True
            IF_JSON_INPUT = True
            IF_JSON_OUTPUT = True

        class Protect(NighttimeWhispers):
            ROLE = "Guard"
            ACTION = "PROTECT"
            IF_RENEW = True
            IF_JSON_INPUT = True
            IF_JSON_OUTPUT = True

        class Verify(NighttimeWhispers):
            ROLE = "Seer"
            ACTION = "VERIFY"
            IF_RENEW = True
            IF_JSON_INPUT = True
            IF_JSON_OUTPUT = True

        class Save(NighttimeWhispers):
            ROLE = "Witch"
            ACTION = "SAVE"
            IF_RENEW = True
            IF_JSON_INPUT = True
            IF_JSON_OUTPUT = True

            def subclass_renew_prompt(self, prompt_json):
                del prompt_json['ACTION']
                del prompt_json['ATTENTION']

                prompt_json["OUTPUT_FORMAT"]["THOUGHTS"] = "It is night time. Return the thinking steps of your decision of whether to save the player JUST be killed at this night."
                prompt_json["OUTPUT_FORMAT"]["OUTPUT"] = "Follow the Moderator's instruction, decide whether you want to save that person or not. Return SAVE or PASS."

                return prompt_json

        class Poison(NighttimeWhispers):
            ROLE = "Witch"
            ACTION = "POISON"
            IF_RENEW = True
            IF_JSON_INPUT = True
            IF_JSON_OUTPUT = True

            def subclass_renew_prompt(self, prompt_json):
                prompt_json["OUTPUT_FORMAT"]["OUTPUT"] += "Or if you want to PASS, then return PASS."
                return prompt_json

    """

    ROLE = "Werewolf"
    ACTION = "KILL"
    IF_RENEW = True
    IF_JSON_INPUT = True
    IF_JSON_OUTPUT = True
    PROMPT_TEMPLATE = """
    {
    "ROLE": "__role__"
    ,"ACTION": "Choose one living player to __action__."
    ,"ATTENTION": "You can only __action__ a player who is alive at this night! And you can not __action__ a player who is dead as this night!"
    ,"PHASE": "Night"
    ,"BACKGROUND": "It's a werewolf game and you are a __role__. Here's the game history:{__context__}."
    ,"OUTPUT_FORMAT":
        {
        "ROLE": "Your role."
        ,"NUMBER": "Your player number."
        ,"IDENTITY": "You are? What is you identity? You are player1 or player2 or player3 or player4 or player5 or player6 or player7?"        
        ,"LIVING_PLAYERS": "List the players who is alive. Return a LIST datatype."
        ,"THOUGHTS": "It is night time. Return the thinking steps of your decision of choosing one living player from `LIVING_PLAYERS` to __action__ this night. And return the reason why you choose to __action__ this player."
        ,"OUTPUT": "As a __role__, you should choose one living player from `LIVING_PLAYERS` to __action__ this night according to the THOUGHTS you have just now. Return the number of the player you choose and return this NUMBER ONLY."
        }
    }
    """

    def __init__(self, name="NightTimeWhispers", context=None, llm=None):
        super().__init__(name, context, llm)

    def _renew_prompt_json(self, prompt_json: dict, role: str, action: str, context: str):

        def replace_string(prompt_json: dict):
            k: str
            for k in prompt_json.keys():
                if isinstance(prompt_json[k], dict):
                    prompt_json[k] = replace_string(prompt_json[k])
                    continue
                prompt_json[k] = prompt_json[k].replace("__role__", role)
                prompt_json[k] = prompt_json[k].replace("__action__", action)

            return prompt_json

        prompt_json = replace_string(prompt_json)

        prompt_json["BACKGROUND"] = prompt_json["BACKGROUND"].replace("__context__", context)

        return prompt_json

    def subclass_renew_prompt(self, prompt_json: dict):
        return prompt_json

    async def run(self, context: str):
        """
        Note: `final_prompt` could be undefined and will raise error if `IF_RENEW` is true and `IF_JSON_INPUT` is False
        """

        if not self.IF_RENEW:
            final_prompt = self.PROMPT_TEMPLATE.replace("__context__", context)
            rsp_content = await self._aask(final_prompt)
            return rsp_content

        if self.IF_JSON_INPUT:
            prompt_json = json.loads(self.PROMPT_TEMPLATE)
            prompt_json = self._renew_prompt_json(prompt_json=prompt_json, role=self.ROLE, action=self.ACTION,
                                                  context=context)
            prompt_json = self.subclass_renew_prompt(prompt_json)  # can be defined in subclass
            final_prompt = json.dumps(prompt_json, indent=4, separators=(',', ': '), ensure_ascii=False)

        rsp_content = await self._aask(final_prompt)

        with open(WORKSPACE_ROOT / f'{self.ACTION}.txt', 'a') as f:
            f.write(rsp_content)

        if self.IF_JSON_OUTPUT:
            re_run = 2
            while re_run > 0:
                try:
                    rsp = json.loads(rsp_content)
                    break
                except:
                    re_run -= 1
            return f"{self.ACTION} Player" + str(rsp["OUTPUT"])

        return rsp_content


