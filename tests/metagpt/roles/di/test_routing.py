import asyncio

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.logs import logger
from metagpt.roles import Architect, ProductManager, ProjectManager
from metagpt.roles.di.data_analyst import DataAnalyst
from metagpt.roles.di.engineer2 import Engineer2
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message

NORMAL_QUESTION = [
    "create a 2048 game",
    "write a snake game",
    "Write a 2048 game using JavaScript without using any frameworks, user can play with keyboard.",
    "print statistic summary of sklearn iris dataset",
    "Run data analysis on sklearn Wine recognition dataset, and train a model to predict wine class (20% as validation), and show validation accuracy.",
    """
    Get data from `paperlist` table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,
    and save it to a csv file. paper title must include `multiagent` or `large language model`. *notice: print key variables*
    """,
    """
    Write a fix for this issue: https://github.com/langchain-ai/langchain/issues/20453, 
    you can fix it on this repo https://github.com/garylin2099/langchain,
    checkout a branch named test-fix, commit your changes, push, and create a PR to the master branch of https://github.com/iorisa/langchain
    """,
    ## info searching ##
    """When is the Olympic football final this year, where will it be held, and where can I buy tickets? If possible, please provide me with a link to buy tickets""",
    """Help me search for Inter Miami CF home games in the next 2 months and give me the link to buy tickets""",
    """请为我查找位于深圳大学附近1000米范围内，价格适中（性价比最高），且晚上关门时间晚于22:00的健身房。""",
    "今天的天气怎样",
    "奥运会的开幕式是什么时候",
]

QUICK_QUESTION = [
    ## general knowledge qa, logical, math ##
    """Who is the first man landing on Moon""",
    """In DNA adenine normally pairs with: A. cytosine. B. guanine. C. thymine. D. uracil. Answer:""",
    """________________ occur(s) where there is no prior history of exchange and no future exchanges are expected between a buyer and seller. A. Relationship marketing. B. Service mix. C. Market exchanges. D. Service failure. Answer:""",
    """Within American politics, the power to accord official recognition to other countries belongs to A. the Senate. B. the president. C. the Secretary of State. D. the chairman of the Joint Chiefs. Answer:""",
    """Find the degree for the given field extension Q(sqrt(2), sqrt(3), sqrt(18)) over Q.""",
    """True or false? Statement 1 | A ring homomorphism is one to one if and only if the kernel is {{0}},. Statement 2 | Q is an ideal in R""",
    """Jean has 30 lollipops. Jean eats 2 of the lollipops. With the remaining lollipops, Jean wants to package 2 lollipops in one bag. How many bags can Jean fill?""",
    """Alisa biked 12 miles per hour for 4.5 hours. Stanley biked at 10 miles per hour for 2.5 hours. How many miles did Alisa and Stanley bike in total?""",
    ## function filling (humaneval) ##
    """
    def has_close_elements(numbers: List[float], threshold: float) -> bool:
    ''' Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    '''
    """,
    """
    def is_palindrome(string: str) -> bool:
    ''' Test if given string is a palindrome '''
    return string == string[::-1]


    def make_palindrome(string: str) -> str:
        ''' Find the shortest palindrome that begins with a supplied string.
        Algorithm idea is simple:
        - Find the longest postfix of supplied string that is a palindrome.
        - Append to the end of the string reverse of a string prefix that comes before the palindromic suffix.
        >>> make_palindrome('')
        ''
        >>> make_palindrome('cat')
        'catac'
        >>> make_palindrome('cata')
        'catac'
        '''
    """,
    # casual chat
    """What's your name?""",
    "Who are you",
    "What can you do",
    "Hi",
    "1+1",
    # programming-related but not requiring software development SOP
    "请写一个python入门教程",
    "python里的装饰器是怎么用的，给我个例子",
    "写一个java的hello world程序",
]


async def test_routing_acc():
    role = TeamLeader()

    env = MGXEnv()
    env.add_roles(
        [
            role,
            ProductManager(),
            Architect(),
            ProjectManager(),
            Engineer2(),
            DataAnalyst(),
        ]
    )

    for q in QUICK_QUESTION:
        msg = Message(content=q)
        role.put_message(msg)
        # await env.run()
        await role._observe()
        rsp = await role._quick_think()
        role.rc.memory.clear()
        if not rsp:
            logger.error(f"Quick question failed: {q}")
        # assert rsp

    for q in NORMAL_QUESTION:
        msg = Message(content=q)
        role.put_message(msg)
        await role._observe()
        rsp = await role._quick_think()
        role.rc.memory.clear()
        # assert not rsp
        if rsp:
            logger.error(f"Normal question failed: {q}")


if __name__ == "__main__":
    asyncio.run(test_routing_acc())
