from metagpt.software_company import SoftwareCompany
from metagpt.environment import Environment
from metagpt.actions import BossRequirement as UserRequirement
from metagpt.schema import Message

class WerewolfEnvironment(Environment):

    async def run(self, k=1):
        """处理一次所有信息的运行，各角色顺序执行
        Process all Role runs at once
        """
        for _ in range(k):
            for role in self.roles.values():
                await role.run()

class WerewolfGame(SoftwareCompany):
    """Use the "software company paradigm" to hold a werewolf game"""

    environment = WerewolfEnvironment()

    def start_project(self, idea):
        """Start a project from user instruction."""
        self.idea = idea
        self.environment.publish_message(
            Message(role="User", content=idea, cause_by=UserRequirement, restricted_to="Moderator")
        )
        print("a")
