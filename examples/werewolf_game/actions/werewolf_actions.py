from metagpt.actions import Action
from examples.werewolf_game.actions.common_actions import Speak, NighttimeWhispers


class Hunt(NighttimeWhispers):
    ROLE = "Werewolf"
    ACTION = "KILL"
    IF_RENEW = True
    IF_JSON_INPUT = True
    IF_JSON_OUTPUT = True

class Impersonate(Speak):
    """Action: werewolf impersonating a good guy in daytime speak"""

    PROMPT_TEMPLATE = """
    {
    "BACKGROUND": "It's a Werewolf game, you are __profile__, say whatever possible to increase your chance of win"
    ,"HISTORY": "You have knowledge to the following conversation: __context__"
    ,"ATTENTION": "Try continuously impersonating a role with special ability, such as a Seer or a Witch, in order to mislead
                other players, make them trust you, and thus hiding your werewolf identity. You can not VOTE a player who is NOT ALIVE now!"
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
        ,"SPEECH_OR_VOTE": "Follow the instruction of `YOUR_TURN` above and the `THOUGHTS` you have just now, give a speech or your vote. Remember, you are a WEREWOLF!!! But just keep it in mind, don't tell other players."
        }
    }
    """

    def __init__(self, name="Impersonate", context=None, llm=None):
        super().__init__(name, context, llm)
