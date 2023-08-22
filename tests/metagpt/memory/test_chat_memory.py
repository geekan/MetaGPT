from metagpt.memory.chat_memory import ChatBufferMemory, MessageHistory
from metagpt.schema import AIMessage, Message, SystemMessage, UserMessage


class TestMessageHistory:
    def test_save_message(self):
        history = MessageHistory()
        history.save_message(UserMessage(content="Hello, User!"))
        assert len(history.messages) == 1

    def test_format_message(self):
        history = MessageHistory()

        # When there are no messages to test, it should return an empty string
        assert history.format_message() == ""

        # Testing messages from different roles
        history.save_message(UserMessage(content="Hello, User!"))
        history.save_message(AIMessage(content="Hi, Assistant!"))
        history.save_message(SystemMessage(content="System message"))
        formatted_message = history.format_message()
        assert "user: Hello, User!" in formatted_message
        assert "assistant: Hi, Assistant!" in formatted_message
        assert "system: System message" in formatted_message

        # Testing that messages of other types are ignored
        history.save_message(Message(content="Unknown message"))
        formatted_message = history.format_message()
        assert "Unknown message" not in formatted_message

    def test_get_latest_user_message(self):
        history = MessageHistory()

        # When there are no user messages, it should return a default message
        default_message = history.get_latest_user_message()
        assert default_message.content == "n/a"

        # When there are multiple user messages, it should return the latest user message
        history.save_message(UserMessage(content="User message 1"))
        history.save_message(UserMessage(content="User message 2"))
        latest_user_message = history.get_latest_user_message()
        assert latest_user_message.content == "User message 2"

        # Testing that messages of other types do not affect the result
        history.save_message(AIMessage(content="Assistant message"))
        latest_user_message = history.get_latest_user_message()
        assert latest_user_message.content == "User message 2"

        # After messages are cleared, the default message should be returned
        history.clear()
        latest_user_message = history.get_latest_user_message()
        assert latest_user_message.content == "n/a"

    def test_clear(self):
        history = MessageHistory()
        history.save_message(UserMessage(content="Hello, User!"))
        history.clear()
        assert len(history.messages) == 0


class TestChatBufferMemory:
    def test_save_message_and_get_chat_history(self):
        buffer_memory = ChatBufferMemory()

        # Testing saving and loading messages
        buffer_memory.save_message(UserMessage(content="Message 1"), chat_id=1)
        buffer_memory.save_message(AIMessage(content="Message 2"), chat_id=2)

        chat_1_history = buffer_memory.get_chat_history(chat_id=1)
        chat_2_history = buffer_memory.get_chat_history(chat_id=2)

        assert len(chat_1_history.messages) == 1
        assert len(chat_2_history.messages) == 1

        # Testing loading non-existent chat history
        non_existent_chat_history = buffer_memory.get_chat_history(chat_id=3)
        assert len(non_existent_chat_history.messages) == 0

        # Testing saving multiple messages
        buffer_memory.save_message(UserMessage(content="Message 3"), chat_id=1)
        chat_1_history = buffer_memory.get_chat_history(chat_id=1)
        assert len(chat_1_history.messages) == 2

        # Testing that messages from different chats do not interfere with each other
        buffer_memory.save_message(AIMessage(content="Message 4"), chat_id=2)
        chat_1_history = buffer_memory.get_chat_history(chat_id=1)
        chat_2_history = buffer_memory.get_chat_history(chat_id=2)
        assert len(chat_1_history.messages) == 2
        assert len(chat_2_history.messages) == 2

    def test_clear(self):
        buffer_memory = ChatBufferMemory()
        buffer_memory.save_message(UserMessage(content="Message 1"), chat_id=1)
        buffer_memory.clear()
        assert not buffer_memory.chats
