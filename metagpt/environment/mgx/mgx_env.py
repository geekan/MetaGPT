from metagpt.environment.base_env import Environment
from metagpt.logs import get_human_input
from metagpt.schema import Message


class MGXEnv(Environment):
    """MGX Environment"""

    history: dict[str, Message] = {}  # redefine message history

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

        self.history[message.id] = message

        return True

    def forward_message(self, message_id: str) -> str:
        if message_id not in self.history:
            return f"invalid message_id {message_id}, not found in history."
        msg = self.history[message_id]
        return self._publish_message(msg)

    async def ask_human(self, question: str) -> str:
        # NOTE: Can be overwritten in remote setting
        return get_human_input(question)

    async def reply_to_human(self, message: str) -> str:
        # NOTE: Can be overwritten in remote setting
        return message
