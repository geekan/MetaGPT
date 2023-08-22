from collections import defaultdict
from typing import Any

from pydantic import BaseModel

from metagpt.schema import AIMessage, Message, SystemMessage, UserMessage


class MessageHistory(BaseModel):
    messages: list[Message] = []

    def save_message(self, message: Message) -> None:
        self.messages.append(message)

    def format_message(self) -> str:
        if not self.messages:
            return ""

        string_messages = [
            f"{m.instruct_content}: {m.content}"
            for m in self.messages
            if isinstance(m, (UserMessage, AIMessage, SystemMessage))
        ]
        return "\n".join(string_messages) + "\n"

    def get_latest_user_message(self) -> UserMessage:
        for message in reversed(self.messages):
            if isinstance(message, UserMessage):
                return message
        return UserMessage(content="n/a")

    def clear(self) -> None:
        self.messages = []


class ChatBufferMemory(BaseModel):
    """Buffer for storing conversation memory"""

    chats: dict[Any, MessageHistory] = defaultdict(MessageHistory)

    def save_message(self, message: Message, chat_id=None) -> None:
        self.chats[chat_id].save_message(message)

    def get_chat_history(self, chat_id=None) -> MessageHistory:
        return self.chats.get(chat_id, MessageHistory())

    def clear(self) -> None:
        self.chats = {}
