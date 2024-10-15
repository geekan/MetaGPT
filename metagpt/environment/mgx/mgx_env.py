from __future__ import annotations

from metagpt.const import AGENT, IMAGES, MESSAGE_ROUTE_TO_ALL, TEAMLEADER_NAME
from metagpt.environment.base_env import Environment
from metagpt.logs import get_human_input
from metagpt.roles import Role
from metagpt.schema import Message, SerializationMixin
from metagpt.utils.common import extract_and_encode_images


class MGXEnv(Environment, SerializationMixin):
    """MGX Environment"""

    direct_chat_roles: set[str] = set()  # record direct chat: @role_name

    is_public_chat: bool = True

    def _publish_message(self, message: Message, peekable: bool = True) -> bool:
        if self.is_public_chat:
            message.send_to.add(MESSAGE_ROUTE_TO_ALL)
        message = self.move_message_info_to_content(message)
        return super().publish_message(message, peekable)

    def publish_message(self, message: Message, user_defined_recipient: str = "", publicer: str = "") -> bool:
        """let the team leader take over message publishing"""
        message = self.attach_images(message)  # for multi-modal message

        tl = self.get_role(TEAMLEADER_NAME)  # TeamLeader's name is Mike

        if user_defined_recipient:
            # human user's direct chat message to a certain role
            for role_name in message.send_to:
                if self.get_role(role_name).is_idle:
                    # User starts a new direct chat with a certain role, expecting a direct chat response from the role; Other roles including TL should not be involved.
                    # If the role is not idle, it means the user helps the role with its current work, in this case, we handle the role's response message as usual.
                    self.direct_chat_roles.add(role_name)

            self._publish_message(message)
            # # bypass team leader, team leader only needs to know but not to react (commented out because TL doesn't understand the message well in actual experiments)
            # tl.rc.memory.add(self.move_message_info_to_content(message))

        elif message.sent_from in self.direct_chat_roles:
            # if chat is not public, direct chat response from a certain role to human user, team leader and other roles in the env should not be involved, no need to publish
            self.direct_chat_roles.remove(message.sent_from)
            if self.is_public_chat:
                self._publish_message(message)

        elif publicer == tl.profile:
            if message.send_to == {"no one"}:
                # skip the dummy message from team leader
                return True
            # message processed by team leader can be published now
            self._publish_message(message)

        else:
            # every regular message goes through team leader
            message.send_to.add(tl.name)
            self._publish_message(message)

        self.history.add(message)

        return True

    async def ask_human(self, question: str, sent_from: Role = None) -> str:
        # NOTE: Can be overwritten in remote setting
        rsp = await get_human_input(question)
        return "Human response: " + rsp

    async def reply_to_human(self, content: str, sent_from: Role = None) -> str:
        # NOTE: Can be overwritten in remote setting
        return "SUCCESS, human has received your reply. Refrain from resending duplicate messages.  If you no longer need to take action, use the command ‘end’ to stop."

    def move_message_info_to_content(self, message: Message) -> Message:
        """Two things here:
        1. Convert role, since role field must be reserved for LLM API, and is limited to, for example, one of ["user", "assistant", "system"]
        2. Add sender and recipient info to content, making TL aware, since LLM API only takes content as input
        """
        converted_msg = message.model_copy(deep=True)
        if converted_msg.role not in ["system", "user", "assistant"]:
            converted_msg.role = "assistant"
        sent_from = converted_msg.metadata[AGENT] if AGENT in converted_msg.metadata else converted_msg.sent_from
        # When displaying send_to, change it to those who need to react and exclude those who only need to be aware, e.g.:
        # send_to={<all>} -> Mike; send_to={Alice} -> Alice; send_to={Alice, <all>} -> Alice.
        if converted_msg.send_to == {MESSAGE_ROUTE_TO_ALL}:
            send_to = TEAMLEADER_NAME
        else:
            send_to = ", ".join({role for role in converted_msg.send_to if role != MESSAGE_ROUTE_TO_ALL})
        converted_msg.content = f"[Message] from {sent_from or 'User'} to {send_to}: {converted_msg.content}"
        return converted_msg

    def attach_images(self, message: Message) -> Message:
        if message.role == "user":
            images = extract_and_encode_images(message.content)
            if images:
                message.add_metadata(IMAGES, images)
        return message

    def __repr__(self):
        return "MGXEnv()"
