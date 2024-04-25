from metagpt.environment.base_env import Environment
from metagpt.logs import get_human_input
from metagpt.schema import Message


class MGXEnv(Environment):
    """MGX Environment"""

    def _publish_message(self, message: Message, peekable: bool = True) -> bool:
        return super().publish_message(message, peekable)

    def publish_message(self, message: Message, user_defined_recipient: str = "", publicer: str = "") -> bool:
        """let the team leader take over message publishing"""
        tl = self.get_role("Team Leader")

        if user_defined_recipient:
            self._publish_message(message)
            # bypass team leader, team leader only needs to know but not to react
            tl.rc.memory.add(message)

        elif publicer == tl.profile:
            # message processed by team leader can be published now
            self._publish_message(message)

        else:
            # every regular message goes through team leader
            tl.put_message(message)

        return True

    async def ask_human(self, question: str) -> str:
        # NOTE: Can be overwritten in remote setting
        return get_human_input(question)

    async def reply_to_human(self, content: str) -> str:
        # NOTE: Can be overwritten in remote setting
        return content
