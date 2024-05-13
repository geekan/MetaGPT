import asyncio
import os
import threading

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.roles import Architect, Engineer, ProductManager, ProjectManager
from metagpt.roles.di.data_analyst import DataAnalyst
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message


async def main(requirement="", enable_human_input=False):
    env = MGXEnv()
    env.add_roles(
        [
            TeamLeader(),
            ProductManager(),
            Architect(),
            ProjectManager(),
            Engineer(n_borg=5, use_code_review=False),
            # QaEngineer(),
            DataAnalyst(tools=["<all>"]),
        ]
    )

    if enable_human_input:
        # simulate human sending messages in chatbox
        send_human_input(env)

    if requirement:
        env.publish_message(Message(content=requirement))
        # env.publish_message(Message(content=requirement, send_to={"David"}), user_defined_recipient="David")

    while not env.is_idle:
        await env.run()


def send_human_input(env):
    """
    Simulate sending message in chatbox
    Note in local environment, the message is consumed only after current round of env.run is finished
    """

    def send_messages():
        while True:
            message = input("Enter a message any time: ")
            env.publish_message(Message(content=message))

    # Start a thread for sending messages
    send_thread = threading.Thread(target=send_messages, args=())
    send_thread.start()


GAME_REQ = "create a 2048 game"
SIMPLE_REQ = "print statistic summary of sklearn iris dataset"
WINE_REQ = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."
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
FIX_ISSUE = """
Write a fix for this issue: https://github.com/langchain-ai/langchain/issues/20453, 
you can fix it on this repo https://github.com/garylin2099/langchain,
checkout a branch named test-fix, commit your changes, push, and create a PR to the master branch of https://github.com/iorisa/langchain
"""
FIX_ISSUE_SIMPLE = """
Write a fix for this issue: https://github.com/mannaandpoem/simple_calculator/issues/1, 
you can fix it on this repo https://github.com/garylin2099/simple_calculator,
checkout a branch named test, commit your changes, push, and create a PR to the original repo.
"""
PUSH_PR_REQ = """
clone https://github.com/garylin2099/simple_calculator, checkout a new branch named test-branch, add an empty file test_file.py to the repo.
Commit your changes and push, finally, create a PR to the master branch of https://github.com/mannaandpoem/simple_calculator.
"""


if __name__ == "__main__":
    # NOTE: Add access_token to test github issue fixing
    os.environ["access_token"] = "ghp_xxx"
    # NOTE: Change the requirement to the one you want to test
    #       Set enable_human_input to True if you want to simulate sending messages in chatbox
    asyncio.run(main(requirement=FIX_ISSUE, enable_human_input=False))
