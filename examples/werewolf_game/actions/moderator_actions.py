import collections

from metagpt.actions import Action

ROLE_STATES = {
    # 存活状态
    0: "Alive", # 开场
    1: "Dead", # 结束
    2: "Protected", # 被保护
    3: "Poisoned", # 被毒
    4: "Saved", # 被救
    5: "Killed" # 被刀
}

STAGE_INSTRUCTIONS = {
    # 上帝需要介入的全部步骤和对应指令
    # The 1-st night
    0: {"content": "It’s dark, everyone close your eyes. I will talk with you/your team secretly at night.",
        "send_to": "Moderator", # for moderator to continuen speaking
        "restricted_to": ""},
    1: {"content": "Werewolves, please open your eyes!",
        "send_to": "Moderator", # for moderator to continuen speaking
        "restricted_to": ""},
    2: {"content": """Werewolves, I secretly tell you that Player 3 and Player 4 are
                   all of the 2 werewolves! Keep in mind you are teammates. The rest players are not werewolves.
                   choose one from the following living options please:
                   [Player 1, Player2]. """, # send to werewolf restrictedly for a response
        "send_to": "Werewolf",
        "restricted_to": "Werewolf"},
    3: {"content": "Werewolves, close your eyes",
        "send_to": "Moderator", # for moderator to continuen speaking
        "restricted_to": ""},
    4: {"content": """It's daytime. No one dies last night. Now freely talk about roles of other players with each other based on your observation and reflection
                   with few sentences. Decide whether to reveal your identity based on your reflection.""",
        "send_to": "", # send to all to speak in daytime
        "restricted_to": ""}
}

VOTE_PROMPT = """
    Welcome to the daytime discussion phase in the Werewolf game.
    
    During the day, players discuss and share information about who they suspect might be a werewolf.
    Players can also cast their votes to eliminate a player they believe is a werewolf.
    
    Here are the conversations from the daytime:
    
    {vote_message}
    
    Now it's time to cast your votes.
    
    You can vote for a player by typing their name.
    Example: "Vote for Player2"
    
    Here are the voting options:

"""

PARSE_INSTRUCTIONS = {

    0: {"Now it's time to vote"},
    1: {"The {winner} have won! They successfully eliminated all the {loser}}."
        "The game has ended. Thank you for playing Werewolf!"},
    2: {"The night has ended, and it's time to reveal the casualties."
        "During the night, the Werewolves made their move. Unfortunately, they targeted {PlayerName}, who is now dead."}

}

class InstructSpeak(Action):
    def __init__(self, name="InstructSpeak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, stage_idx):
        return STAGE_INSTRUCTIONS[stage_idx]

class ParseSpeak(Action):
    def __init__(self, name="ParseSpeak", context=None, llm=None):
        super().__init__(name, context, llm)
        self.daytime_info = collections.defaultdict(list)
        self.night_info = collections.defaultdict(list)
        self.vote_message = []

    async def run(self, dead_history, context, env):

        for m in env.memory.get():
            role = m.sent_from if hasattr(m, 'sent_from') else ""
            content = m.content if hasattr(m, 'content') else ""
            target = m.sent_to if hasattr(m, 'sent_to') else ""
            restricted = m.restricted_to if hasattr(m, 'restricted_to') else ""
            if target == 'all':
                self.daytime_info[role] = [content, target, restricted]
            else:
                self.night_info[role] = [content, target, restricted]

        # collect info from the night and identify the dead player
        for role in self.night_info:
            if "kill" in self.night_info[role][0] and self.night_info[role][1]:
                target = self.night_info[role][1]
                print("env.get_roles[target]", env, env.env.roles)
                env.env.roles[target].set_status(ROLE_STATES[5])
        for role in self.night_info:
            if ("save" or "guard") in self.night_info[role][0]:
                save_target = self.night_info[role][1]
                if save_target == target:
                    env.env.roles[target].set_status(ROLE_STATES[0])
                else:
                    dead_history.append(target)

        # collect message from the daytime and identify the vote player
        for role in self.daytime_info:
            self.vote_message += f"\n{self.daytime_info[role][0]}"

        vote_player = await self.llm.aask(VOTE_PROMPT.format(vote_message=self.vote_message))
        dead_history.append(vote_player)

        return dead_history, vote_player, PARSE_INSTRUCTIONS

class SummarizeNight(Action):
    """consider all events at night, conclude which player dies (can be a peaceful night)"""
    pass

class SummarizeDay(Action):
    """consider all votes at day, conclude which player dies"""
    pass

class AnnounceGameResult(Action):

    async def run(self, winner: str):
        return f"Game over! The winner is {winner}"
