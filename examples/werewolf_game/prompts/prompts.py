# 论文中出现的提示语，利用了思维链
# 1. 基于游戏规则和对话内容，选择5个问题
# 2. 生成2个问题
# 3. 生成可能的回答
# 4. 进行反思
# 5. 生成最终回复

GAME_RULE = '''You are playing a game called the Werewolf with some other players. This game is based on text conversations. Here are
the game rules: Roles: The moderator is also host, he organised this game and you need to answer his instructions correctly.
Don’t talk with the moderator. There are five roles in the game, werewolf, villager, seer, guard and witch. There are two
alternate phases in this game, daytime and dark. When it’s dark: Your talking content with moderator is confidential. You
needn’t worry about other players and moderator knowing what you say and do. No need to worry about suspicions from
others during the night. If you are werewolf, you can know what your teammates want to kill and you should vote one player
to kill based on your analysis. Player who receives the most votes after all werewolves voting will be killed. No one will be
killed if there is no consensus! If you are witch, you have a bottle of antidote that can save a player targeted by werewolves
after dark, and a bottle of poison that can poison a player after dark. Both poison and antidote can be used only once. If you
are seer, you can verify whether a player is a werewolf every night, which is a very important thing. If you are guard, you
can protect a player every night to prevent the player from being killed by werewolves, but guard cannot resist the witch’s
poison and guard cannot protect the same player on two consecutive nights. Villagers can’t do anything at night. During the
daytime: you discuss with all players including your enemies. At the end of the discussion, players vote to eliminate one
player they suspect of being a werewolf. The player with the most votes will be eliminated. The moderator will tell who is
killed, otherwise there is no one killed. Note that villager, seer, guard and witch are all in villager side, they have the same
objective. Objectives: If you are werewolf, your goal is to cooperate with other werewolves to kill all players who are not
werewolves at last. If you are not werewolf, you need to kill all werewolves with your partner once you find out that certain
players are suspicious to be werewolves. This could greatly improve your chances of winning, although it is somewhat risky.If
one player is killed, he can’t do anything anymore and will be out of the game. Tips: To complete the objective: During
night, you should analyze and use your ability correctly. During daytime, you need to reason carefully about the roles of other
players and be careful not to reveal your own role casually unless you’re cheating other players. Only give the player’s name
when making a decision/voting, and don’t generate other players’ conversation.Reasoning based on facts you have observed
and you cannot perceive information (such as acoustic info) other than text. You are Player {name}, the {profile}.
You’re playing with 6 other players. Do not pretend you are other players or the moderator.
'''

SELECT_QUESTIONS = '''
Now its the {t}-th {day_or_night}. Given the game rules and conversations above, assuming you are {agent_name}, the
{role}, and to complete the instructions of the moderator, you need to think about a few questions clearly first, so that you can
make an accurate decision on the next step. Choose only five that you think are the most important in the current situation
from the list of questions below: {questions_prepared_for_specific_role} Please repeat the five important questions of your
choice, separating them with ‘##’.
'''

# 为特定的角色，准备的问题
questions_prepared_for_specific_role_sample = '''
1. What is my player name and what is my role? What is my final objective in this game?
2. Based on the chat history, can you guess what some players’ role might be?
3. What is the current phase, daytime or night? what should I do at this phase according to the game rules?
4. Based on the conversation and my inference, who is most likely to be an alive werewolf? 
5. I want to know who the most suspicious player, and why?
6. I also want to know if any player’s behavior has changed suspiciously compared to the previous days, and if so, who and why?
7. What is the best strategy I should use right now to uncover werewolves without revealing my own role? Should I accuse someone directly, ask probing questions, or stay silent for now?
8. Have any players claimed specific roles that can be verified or disputed? 
'''

ASK_QUESTIONS = '''
Now its the {t}-th {day_or_night}. Given the game rules and conversations above, assuming you are {agent_name}, the
{role}, and to complete the instructions of the moderator, you need to think about a few questions clearly first, so that you can
make an accurate decision on the next step. {selected_questions} Do not answer these queations. In addition to the above
questions, please make a bold guess, what else do you want to know about the current situation? Please ask two important
questions in first person, separating them with ‘##’.
'''

GENERATE_POSSIBLE_ANSWER = '''
Now its the {t}-th {day_or_night}. Given the game rules and conversations above, assuming you are {agent_name}, the
{role}, for question: {question} There are some possible answers: {candidate_answers} Generate the correct answer
based on the context. If there is not direct answer, you should think and generate the answer based on the context. No need to
give options. The answer should in first person using no more than 2 sentences and without any analysis and item numbers.
'''

REFLECTION = '''
Now its the {t}-th {day_or_night}. Assuming you are {agent_name}, the {role}, what insights can you summarize
with few sentences based on the above conversations and {At} in heart for helping continue the talking and achieving your
objective? For example: As the {role}, I observed that... I think that... But I am... So...
'''

# 得到最终的回复，再抽取出最终的content
GENERATE_FINAL_RESPONSE = '''
Now its the {t}-th {day_or_night}. Think about what to say based on the game rules and context, especially the just now
reflection {R}.  
Give your step-by-step thought process and your derived consise talking content (no more than 2 sentences) at last, separating them with ‘##’.
For example: 
## Thought process
My step-by-step thought process:... 
## Content
My concise talking content: ...
'''
