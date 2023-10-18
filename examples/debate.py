'''
Filename: MetaGPT/examples/debate.py
Created Date: Tuesday, September 19th 2023, 6:52:25 pm
Author: garylin2099
'''
import asyncio
import platform
import fire

from metagpt.software_company import SoftwareCompany
from metagpt.actions import Action, BossRequirement
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

class ShoutOut(Action):
    """Action: Shout out loudly in a debate (quarrel)"""

    PROMPT_TEMPLATE = """
    ## BACKGROUND
    Suppose you are {name}, you are in a debate with {opponent_name}.
    ## DEBATE HISTORY
    Previous rounds:
    {context}
    ## YOUR TURN
    Now it's your turn, you should closely respond to your opponent's latest argument, state your position, defend your arguments, and attack your opponent's arguments,
    craft a strong and emotional response in 80 words, in {name}'s rhetoric and viewpoints, your will argue:
    """

    def __init__(self, name="ShoutOut", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context: str, name: str, opponent_name: str):

        prompt = self.PROMPT_TEMPLATE.format(context=context, name=name, opponent_name=opponent_name)
        # logger.info(prompt)

        rsp = await self._aask(prompt)

        return rsp

class Trump(Role):
    def __init__(
        self,
        name: str = "Trump",
        profile: str = "Republican",
        **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        self._init_actions([ShoutOut])
        self._watch([ShoutOut])
        self.name = "Trump"
        self.opponent_name = "Biden"

    async def _observe(self) -> int:
        await super()._observe()
        # accept messages sent (from opponent) to self, disregard own messages from the last round
        self._rc.news = [msg for msg in self._rc.news if msg.send_to == self.name]  
        return len(self._rc.news)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")

        msg_history = self._rc.memory.get_by_actions([ShoutOut])
        context = []
        for m in msg_history:
            context.append(str(m))
        context = "\n".join(context)

        rsp = await ShoutOut().run(context=context, name=self.name, opponent_name=self.opponent_name)

        msg = Message(
            content=rsp,
            role=self.profile,
            cause_by=ShoutOut,
            sent_from=self.name,
            send_to=self.opponent_name,
        )

        return msg

class Biden(Role):
    def __init__(
        self,
        name: str = "Biden",
        profile: str = "Democrat",
        **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        self._init_actions([ShoutOut])
        self._watch([BossRequirement, ShoutOut])
        self.name = "Biden"
        self.opponent_name = "Trump"

    async def _observe(self) -> int:
        await super()._observe()
        # accept the very first human instruction (the debate topic) or messages sent (from opponent) to self,
        # disregard own messages from the last round
        self._rc.news = [msg for msg in self._rc.news if msg.cause_by == BossRequirement or msg.send_to == self.name]
        return len(self._rc.news)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")

        msg_history = self._rc.memory.get_by_actions([BossRequirement, ShoutOut])
        context = []
        for m in msg_history:
            context.append(str(m))
        context = "\n".join(context)

        rsp = await ShoutOut().run(context=context, name=self.name, opponent_name=self.opponent_name)

        msg = Message(
            content=rsp,
            role=self.profile,
            cause_by=ShoutOut,
            sent_from=self.name,
            send_to=self.opponent_name,
        )

        return msg

async def startup(idea: str, investment: float = 3.0, n_round: int = 5,
                  code_review: bool = False, run_tests: bool = False):
    """We reuse the startup paradigm for roles to interact with each other.
    Now we run a startup of presidents and watch they quarrel. :) """
    company = SoftwareCompany()
    company.hire([Biden(), Trump()])
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


def main(idea: str, investment: float = 3.0, n_round: int = 10):
    """
    :param idea: Debate topic, such as "Topic: The U.S. should commit more in climate change fighting" 
                 or "Trump: Climate change is a hoax"
    :param investment: contribute a certain dollar amount to watch the debate
    :param n_round: maximum rounds of the debate
    :return:
    """
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(startup(idea, investment, n_round))


if __name__ == '__main__':
    fire.Fire(main)
