import asyncio
import platform
import fire

from metagpt.software_company import SoftwareCompany
from metagpt.actions import Action, BossRequirement
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

class Shout(Action):

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

    def __init__(self, name="Shout", context=None, llm=None):
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
        profile: str = "Trump",
        **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        self._init_actions([Shout])
        self._watch([Shout])
        self.name = "Trump"
        self.opponent_name = "Biden"
    
    async def _observe(self) -> int:
        await super()._observe()
        self._rc.news = [
            msg for msg in self._rc.news if msg.send_to == self.name
        ]  # only relevant msgs count as observed news
        return len(self._rc.news)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        
        msg_history = self._rc.memory.get_by_actions([Shout])
        context = []
        for m in msg_history:
            context.append(str(m))
        context = "\n".join(context)

        rsp = await Shout().run(context=context, name=self.name, opponent_name=self.opponent_name)

        msg = Message(
            content=rsp,
            role=self.profile,
            cause_by=Shout,
            sent_from=self.name,
            send_to=self.opponent_name,
        )
        self._publish_message(msg)

        return msg

class Biden(Role):
    def __init__(
        self,
        name: str = "Biden",
        profile: str = "Biden",
        **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        self._init_actions([Shout])
        self._watch([BossRequirement, Shout])
        self.name = "Biden"
        self.opponent_name = "Trump"
    
    async def _observe(self) -> int:
        await super()._observe()
        self._rc.news = [
            msg for msg in self._rc.news if msg.send_to == self.name or msg.cause_by == BossRequirement
        ]  # only relevant msgs count as observed news
        return len(self._rc.news)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        
        msg_history = self._rc.memory.get_by_actions([BossRequirement, Shout])
        context = []
        for m in msg_history:
            context.append(str(m))
        context = "\n".join(context)

        rsp = await Shout().run(context=context, name=self.name, opponent_name=self.opponent_name)

        msg = Message(
            content=rsp,
            role=self.profile,
            cause_by=Shout,
            sent_from=self.name,
            send_to=self.opponent_name,
        )
        self._publish_message(msg)

        return msg

async def startup(idea: str, investment: float = 3.0, n_round: int = 5,
                  code_review: bool = False, run_tests: bool = False):
    """Run a startup of presidents. Watch they quarrel. :) """
    company = SoftwareCompany()
    company.hire([Biden(), Trump()])
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


def main(idea: str, investment: float = 3.0, n_round: int = 10, code_review: bool = False, run_tests: bool = False):
    """
    We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.
    :param idea: Your innovative idea, such as "Creating a snake game."
    :param investment: As an investor, you have the opportunity to contribute a certain dollar amount to this AI company.
    :param n_round:
    :param code_review: Whether to use code review.
    :return:
    """
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(startup(idea, investment, n_round, code_review, run_tests))


if __name__ == '__main__':
    fire.Fire(main)
