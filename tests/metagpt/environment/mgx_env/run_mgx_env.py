import asyncio
import os
import re
import threading
import time

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.roles import Architect, Engineer, ProductManager, ProjectManager
from metagpt.roles.di.data_analyst import DataAnalyst
from metagpt.roles.di.engineer2 import Engineer2
from metagpt.roles.di.swe_agent import SWEAgent
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message


async def main(requirement="", enable_human_input=False, use_fixed_sop=False, allow_idle_time=30):
    if use_fixed_sop:
        engineer = Engineer(n_borg=5, use_code_review=False)
    else:
        engineer = Engineer2()

    env = MGXEnv(allow_bypass_team_leader=use_fixed_sop)
    env.add_roles(
        [
            TeamLeader(),
            ProductManager(use_fixed_sop=use_fixed_sop),
            Architect(use_fixed_sop=use_fixed_sop),
            ProjectManager(use_fixed_sop=use_fixed_sop),
            engineer,
            # QaEngineer(),
            DataAnalyst(),
            SWEAgent(),
        ]
    )

    if enable_human_input:
        # simulate human sending messages in chatbox
        stop_event = threading.Event()
        human_input_thread = send_human_input(env, stop_event)

    if requirement:
        env.publish_message(Message(content=requirement))
        # user_defined_recipient = "Alex"
        # env.publish_message(Message(content=requirement, send_to={user_defined_recipient}), user_defined_recipient=user_defined_recipient)

    allow_idle_time = allow_idle_time if enable_human_input else 1
    start_time = time.time()
    while time.time() - start_time < allow_idle_time:
        if not env.is_idle:
            await env.run()
            start_time = time.time()  # reset start time

    if enable_human_input:
        print("No more human input, terminating, press ENTER for a full termination.")
        stop_event.set()
        human_input_thread.join()


def send_human_input(env, stop_event):
    """
    Simulate sending message in chatbox
    Note in local environment, the message is consumed only after current round of env.run is finished
    """

    def send_messages():
        while not stop_event.is_set():
            message = input("Enter a message any time: ")
            user_defined_recipient = re.search(r"@(\w+)", message)
            if user_defined_recipient:
                recipient_name = user_defined_recipient.group(1)
                print(f"{recipient_name} will receive the message")
                env.publish_message(
                    Message(content=message, send_to={recipient_name}), user_defined_recipient=recipient_name
                )
            else:
                env.publish_message(Message(content=message))

    # Start a thread for sending messages
    send_thread = threading.Thread(target=send_messages, args=())
    send_thread.start()
    return send_thread


GAME_REQ = "create a 2048 game"
WEB_GAME_REQ = "Write a 2048 game using JavaScript without using any frameworks, user can play with keyboard."
WEB_GAME_REQ_DEPLOY = "Write a 2048 game using JavaScript without using any frameworks, user can play with keyboard. When finished, deploy the game to public at port 8090."
SIMPLE_REQ = "print statistic summary of sklearn iris dataset"
WINE_REQ = "Run data analysis on sklearn Wine recognition dataset, and train a model to predict wine class (20% as validation), and show validation accuracy."
PAPER_LIST_REQ = """
Get data from `paperlist` table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,
and save it to a csv file. paper title must include `multiagent` or `large language model`. *notice: print key variables*
"""
ECOMMERCE_REQ = """
Get products data from website https://scrapeme.live/shop/ and save it as a csv file.
**Notice: Firstly parse the web page encoding and the text HTML structure;
The first page product name, price, product URL, and image URL must be saved in the csv;**
"""
data_path = "data/titanic"
train_path = f"{data_path}/split_train.csv"
eval_path = f"{data_path}/split_eval.csv"
TITANIC_REQ = f"This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '{train_path}', eval data path: '{eval_path}'."
FIX_ISSUE1 = """
Write a fix for this issue: https://github.com/langchain-ai/langchain/issues/20453, 
you can fix it on this repo https://github.com/garylin2099/langchain,
checkout a branch named test-fix, commit your changes, push, and create a PR to the master branch of https://github.com/iorisa/langchain
"""
FIX_ISSUE2 = """
Write a fix for this issue https://github.com/geekan/MetaGPT/issues/1275.
You can fix it on the v0.8-release branch of this repo https://github.com/garylin2099/MetaGPT,
during fixing, checkout a branch named test-fix-1275, commit your changes, push, and create a PR to the v0.8-release branch of https://github.com/garylin2099/MetaGPT
"""
FIX_ISSUE3 = """
Write a fix for this issue https://github.com/geekan/MetaGPT/issues/1262.
You can fix it on this repo https://github.com/garylin2099/MetaGPT,
during fixing, checkout a branch named test-fix-1262, commit your changes, push, and create a PR to https://github.com/garylin2099/MetaGPT
"""
FIX_ISSUE_SIMPLE = """
Write a fix for this issue: https://github.com/mannaandpoem/simple_calculator/issues/1, 
you can fix it on this repo https://github.com/garylin2099/simple_calculator,
checkout a branch named test, commit your changes, push, and create a PR to the master branch of original repo.
"""
PUSH_PR_REQ = """
clone https://github.com/garylin2099/simple_calculator, checkout a new branch named test-branch, add an empty file test_file.py to the repo.
Commit your changes and push, finally, create a PR to the master branch of https://github.com/mannaandpoem/simple_calculator.
"""

TL_CHAT1 = """Summarize the paper for me"""  # expecting clarification
TL_CHAT2 = """Solve the issue at this link"""  # expecting clarification
TL_CHAT3 = """Who is the first man landing on Moon"""  # expecting answering directly
TL_CHAT4 = """Find all zeros in the indicated finite field of the given polynomial with coefficients in that field. x^5 + 3x^3 + x^2 + 2x in Z_5"""  # expecting answering directly
TL_CHAT5 = """Find the degree for the given field extension Q(sqrt(2), sqrt(3), sqrt(18)) over Q."""  # expecting answering directly
TL_CHAT6 = """True or False? Statement 1 | A ring homomorphism is one to one if and only if the kernel is {{0}},. Statement 2 | Q is an ideal in R"""  # expecting answering directly
TL_CHAT7 = """Jean has 30 lollipops. Jean eats 2 of the lollipops. With the remaining lollipops, Jean wants to package 2 lollipops in one bag. How many bags can Jean fill?"""  # expecting answering directly
TL_CHAT9 = """What's your name?"""
TL_CHAT10 = "Hi"
TL_CHAT11 = "Tell me about your team"

if __name__ == "__main__":
    # NOTE: Add access_token to test github issue fixing
    os.environ["access_token"] = "ghp_xxx"
    # NOTE: Change the requirement to the one you want to test
    #       Set enable_human_input to True if you want to simulate sending messages in chatbox
    asyncio.run(main(requirement=GAME_REQ, enable_human_input=False, use_fixed_sop=False))
