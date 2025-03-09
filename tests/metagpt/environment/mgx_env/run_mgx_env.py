import asyncio
import os
import re
import threading
import time

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.roles import Architect, Engineer, ProductManager, ProjectManager
from metagpt.roles.di.data_analyst import DataAnalyst
from metagpt.roles.di.engineer2 import Engineer2
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message


async def main(requirement="", enable_human_input=False, use_fixed_sop=False, allow_idle_time=30):
    if use_fixed_sop:
        engineer = Engineer(n_borg=5, use_code_review=False)
    else:
        engineer = Engineer2()

    env = MGXEnv()
    env.add_roles(
        [
            TeamLeader(),
            ProductManager(use_fixed_sop=use_fixed_sop),
            Architect(use_fixed_sop=use_fixed_sop),
            ProjectManager(use_fixed_sop=use_fixed_sop),
            engineer,
            # QaEngineer(),
            DataAnalyst(),
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
GAME_REQ_ZH = "写一个贪吃蛇游戏"
WEB_GAME_REQ = "Write a 2048 game using JavaScript without using any frameworks, user can play with keyboard."
WEB_GAME_REQ_DEPLOY = "Write a 2048 game using JavaScript without using any frameworks, user can play with keyboard. When finished, deploy the game to public at port 8090."
TODO_APP_REQ = "Create a website widget for TODO list management. Users should be able to add, mark as complete, and delete tasks. Include features like prioritization, due dates, and categories. Make it visually appealing, responsive, and user-friendly. Use HTML, CSS, and JavaScript. Consider additional features like notifications or task export. Keep it simple and enjoyable for users.dont use vue or react.dont use third party library, use localstorage to save data."
FLAPPY_BIRD_REQ = "write a flappy bird game in pygame, code only"
SIMPLE_DATA_REQ = "load sklearn iris dataset and print a statistic summary"
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
NEWS_36KR_REQ = """从36kr创投平台https://pitchhub.36kr.com/financing-flash 所有初创企业融资的信息, **注意: 这是一个中文网站**;
下面是一个大致流程, 你会根据每一步的运行结果对当前计划中的任务做出适当调整:
1. 爬取并本地保存html结构;
2. 直接打印第7个*`快讯`*关键词后2000个字符的html内容, 作为*快讯的html内容示例*;
3. 反思*快讯的html内容示例*中的规律, 设计正则匹配表达式来获取*`快讯`*的标题、链接、时间;
4. 筛选最近3天的初创企业融资*`快讯`*, 以list[dict]形式打印前5个。
5. 将全部结果存在本地csv中
**Notice: view the page element before writing scraping code**
"""
data_path = "data/titanic"
train_path = f"{data_path}/split_train.csv"
eval_path = f"{data_path}/split_eval.csv"
TITANIC_REQ = f"This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '{train_path}', eval data path: '{eval_path}'."
CALIFORNIA_HOUSING_REQ = """
Analyze the 'Canifornia-housing-dataset' using https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html#sklearn.datasets.fetch_california_housing to predict the median house value. you need to perfrom data preprocessing, feature engineering and finally modeling to predict the target. Use machine learning techniques such as linear regression (including ridge regression and lasso regression), random forest, XGBoost. You also need to report the MSE on the test dataset
"""
STOCK_REQ = """Import NVIDIA Corporation (NVDA) stock price data from Yahoo Finance, focusing on historical closing prices from the past 5 years.
Summary statistics (mean, median, standard deviation, etc.) to understand the central tendency and dispersion of closingprices. Analyze the data for any noticeable trends, patterns, or anomalies over time, potentially using rolling averages or percentage changes.
Create a pot to visualize all the data analysis. Reserve 20% of the dataset for validaation. Train a predictive model on the training set. Report the modeel's validation accuracy, and visualize the result of prediction result.
"""
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
IMAGE2CODE_REQ = "Please write a frontend web page similar to this image /Users/gary/Files/temp/workspace/temp_img.png, I want the same title and color. code only"
DOC_QA_REQ1 = "Tell me what this paper is about /Users/gary/Files/temp/workspace/2308.09687.pdf"
DOC_QA_REQ2 = "Summarize this doc /Users/gary/Files/temp/workspace/2401.14295.pdf"
DOC_QA_REQ3 = "请总结/Users/gary/Files/temp/workspace/2309.04658.pdf里的关键点"
DOC_QA_REQ4 = "这份报表/Users/gary/Files/temp/workspace/9929550.md中，营业收入TOP3产品各自的收入占比是多少"

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
TL_CHAT12 = "What can you do"
CODING_REQ1 = "写一个java的hello world程序"
CODING_REQ2 = "python里的装饰器是什么"
CODING_REQ3 = "python里的装饰器是怎么用的，给我个例子"


if __name__ == "__main__":
    # NOTE: Add access_token to test github issue fixing
    os.environ["access_token"] = "ghp_xxx"
    # NOTE: Change the requirement to the one you want to test
    #       Set enable_human_input to True if you want to simulate sending messages in chatbox
    asyncio.run(main(requirement=GAME_REQ, enable_human_input=False, use_fixed_sop=False))
