import asyncio
from random import random
import re

from metagpt.actions import Action

GAME_RULE = '''
## Game Overview
You're the moderator of a text-based game called Werewolf. Your role is to guide the players, who can be a werewolf, villager, seer, guard, or witch. The game has two phases: night and day.

## Night Phase
During the night, conversations are private. Players use their abilities:
- Werewolves vote to kill a player.
- The witch can save a player targeted by werewolves or poison a player (each ability can be used once).
- The seer can verify if a player is a werewolf.
- The guard can protect a player from being killed by werewolves (but not from the witch's poison).

## Day Phase
During the day, all players discuss and vote to eliminate a suspected werewolf. You'll announce who is killed.

## Roles and Objectives
Werewolves aim to kill all non-werewolves. All other roles aim to eliminate all werewolves. Killed players are out of the game.

## Tips
Players should use their abilities wisely and reason about others' roles. They should only reveal their role strategically.

## Your Role
As Player {name}, the {profile}, you'll provide step-by-step instructions to players in this order: All(Night) -> Werewolf -> All(Daytime) -> All(Discuss) -> All(Vote). Ensure each player understands their instructions before moving on.
'''
# All(Night) -> Guard -> Werewolf -> Witch -> Seer -> All(Daytime) -> All(Discuss) -> All(Vote).

GENERATE_POSSIBLE_ANSWER = '''
Given the game rules and conversations above, assuming you are {name}, the {profile},
Generate the correct answer based on the context. No need to give options. 
The answer should in first role using no more than 2 sentences and without any analysis and item numbers.
The current player status is as follows:
living players:{living_players}, for Werewolf to choose to kill, and for Seer to verify, and for Guard to protect, and for Witch to poison
werewolf players:{werewolf_players}, for Werewolf to know who is the other werewolf
player hunted:{player_hunted}, for Witch to know who is hunted, then decide to save
player current dead:{player_current_dead}, for all players to know who is dead

Response should have the following format(split by ## ):
## Instruction
The 'Instruction' is the instruction from the moderator. It contains the valuable information that the player needs to know. Such as living players, werewolf players, player hunted, player current dead etc.

## Send To
'Send To' specifies the role who will receive and need to process the message. So don't reveal the player's name!
If you want to send the message to all roles, use All. Otherwise, specify the role profile and Moderator. For example, 'Moderator' or 'Werewolf' or 'Seer' etc.

## Restricted To
restricted_to is all roles who can not see the content, but only this role can see and reply the content. Private information is being shared with that role and they must not reveal it to others.
In day, 'Restricted To' = 'All'. In night, 'Restricted To' generally are more a Moderator than 'Send To'. For example, 'Moderator,Werewolf' or 'Moderator,Seer' etc. 

## Day Or Night
'Day Or Night' specifies the time when the message is sent. It should be 'Day' or 'Night'.

Remember, if a role is 'Sent To', they must process and respond. Other roles will be aware of the message but are not required to respond. If a role is 'restricted_to', private information is being shared with that role and they must not reveal it to others.
Attention: Don't reveal the player's identity!
'''


class InstructSpeak(Action):
    def __init__(self, name="InstructSpeak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, player, conversations, living_players, werewolf_players, player_hunted, player_current_dead):
        game_rule = GAME_RULE.format(name=player.name, profile=player.profile)

        prompt = game_rule + str(conversations)[:4000] + GENERATE_POSSIBLE_ANSWER.format(name=player.name,
                                                                                  profile=player.profile,
                                                                                  living_players=living_players,
                                                                                  werewolf_players=werewolf_players,
                                                                                  player_hunted=player_hunted,
                                                                                  player_current_dead=player_current_dead)

        response = await self._aask(prompt)
        # 提取content, send_to, restricted_to
        content = re.search(r"## Instruction\n(.*?)##", response, re.DOTALL).group(1).strip()
        send_to = re.search(r"## Send To\n(.*?)##", response, re.DOTALL).group(1).strip()
        restricted_to = re.search(r"## Restricted To\n(.*?)##", response, re.DOTALL).group(1).strip()
        day_or_night = re.search(r"## Day Or Night\n(.*)", response, re.DOTALL).group(1).strip()
        # FIXME: 将""改为"All"，利于模型生成？
        if send_to == "All":
            send_to = ""
        if restricted_to == "All":
            restricted_to = ""
        return content, send_to, restricted_to, day_or_night


class ParseSpeak(Action):
    def __init__(self, name="ParseSpeak", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self):
        pass


class SummarizeDay(Action):
    """consider all votes at day, conclude which player dies"""

    def __init__(self, name="SummarizeDay", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, votes):
        # 假设votes是一个字典，代表白天投票的结果，key是被投票的玩家，value是得票数
        # 例如：{"Player1": 2, "Player2": 1, "Player3": 1, "Player4": 0}
        # 表示Player1得到2票，Player2和Player3各得到1票，Player4得到0票
        # 若平票，则随机选一个人出局
        if not votes:
            return "No votes were cast. No one was killed."

        max_votes = max(votes.values())
        players_with_max_votes = [player for player, vote_count in votes.items() if vote_count == max_votes]

        if len(players_with_max_votes) == 1:
            eliminated_player = players_with_max_votes[0]
            return f"{eliminated_player} was voted out and eliminated."
        else:
            # 若平票，则随机选一个人出局
            eliminated_player = players_with_max_votes[int(random() * len(players_with_max_votes))]
            return f"There was a tie in the votes. {eliminated_player} was randomly chosen and eliminated."


class AnnounceGameResult(Action):

    async def run(self, winner: str):
        return f"Game over! The winner is the {winner}"


class MockRole:
    def __init__(self):
        self.name = "Moderator"
        self.profile = "Moderator"


if __name__ == '__main__':
    role = MockRole()
    instance = InstructSpeak()
    a, b, c = asyncio.run(instance.run(role, "", "", "", "", ""))
    print(a, b, c)
