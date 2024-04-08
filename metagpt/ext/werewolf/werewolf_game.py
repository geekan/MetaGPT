from metagpt.actions.add_requirement import UserRequirement
from metagpt.environment import Environment
from metagpt.schema import Message
from metagpt.team import Team


class WerewolfEnvironment(Environment):
    timestamp: int = 0

    def publish_message(self, message: Message, add_timestamp: bool = True):
        """向当前环境发布信息
        Post information to the current environment
        """
        # self.message_queue.put(message)
        if add_timestamp:
            # 因消息内容可能重复，例如，连续两晚杀同一个人，
            # 因此需要加一个unique的time_stamp以使得相同的message在加入记忆时不被自动去重
            message.content = f"{self.timestamp} | " + message.content
        self.memory.add(message)
        self.history += f"\n{message}"

    async def run(self, k=1):
        """处理一次所有信息的运行，各角色顺序执行
        Process all Role runs at once
        """
        for _ in range(k):
            for role in self.roles.values():
                await role.run()
            self.timestamp += 1


class WerewolfGame(Team):
    """Use the "software company paradigm" to hold a werewolf game"""

    environment = WerewolfEnvironment()

    def start_project(self, idea):
        """Start a project from user instruction."""
        self.idea = idea
        self.environment.publish_message(
            Message(role="User", content=idea, cause_by=UserRequirement, restricted_to="Moderator")
        )
