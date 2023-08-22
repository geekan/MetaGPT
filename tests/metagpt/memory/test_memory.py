from metagpt.actions import Action
from metagpt.memory import Memory
from metagpt.schema import Message


# Define test cases for the Memory class
class TestMemory:
    def test_add(self):
        memory = Memory()
        message1 = Message(content="Hello")
        message2 = Message(content="Hi there")

        # Add a message
        memory.add(message1)
        assert message1 in memory.storage

        # Add the same message again (should not add duplicate)
        memory.add(message1)
        assert len(memory.storage) == 1

        # Add another message
        memory.add(message2)
        assert message2 in memory.storage
        assert len(memory.storage) == 2

    def test_add_with_cause_by(self):
        memory = Memory()
        action = Action()
        message = Message(content="Hello", cause_by=action)

        # Add a message with a cause_by
        memory.add(message)
        assert message in memory.storage
        assert message in memory.index[action]

        # Add the same message again (should not add duplicate)
        memory.add(message)
        assert len(memory.storage) == 1
        assert len(memory.index[action]) == 1

    def test_add_without_cause_by(self):
        memory = Memory()
        message = Message(content="Hello")

        # Add a message without cause_by
        memory.add(message)
        assert message in memory.storage

        # Add the same message again (should not add duplicate)
        memory.add(message)
        assert len(memory.storage) == 1

    def test_add_batch(self):
        memory = Memory()
        messages = [
            Message(content="Hello"),
            Message(content="Hi"),
        ]
        memory.add_batch(messages)
        assert all(message in memory.storage for message in messages)

    def test_get_by_role(self):
        memory = Memory()
        messages = [
            Message(role="user", content="Hello"),
            Message(role="user", content="How are you?"),
            Message(role="bot", content="Hi"),
        ]
        memory.add_batch(messages)
        assert len(memory.get_by_role("user")) == 2

    def test_get_by_content(self):
        memory = Memory()
        messages = [
            Message(content="Hello"),
            Message(content="Hi there"),
        ]
        memory.add_batch(messages)
        assert len(memory.get_by_content("Hi")) == 1

    def test_delete(self):
        memory = Memory()
        message1 = Message(content="Hello")
        message2 = Message(content="Hi there")

        # Add messages
        memory.add(message1)
        memory.add(message2)

        # Delete the first message
        memory.delete(message1)
        assert message1 not in memory.storage
        assert message1 not in memory.index[message1.cause_by]

        # Try to delete the same message again (should not raise an error)
        memory.delete(message1)
        assert message1 not in memory.storage
        assert message1 not in memory.index[message1.cause_by]

        # Delete the second message
        memory.delete(message2)
        assert message2 not in memory.storage

    def test_delete_with_cause_by(self):
        memory = Memory()
        action = Action()
        message = Message(content="Hello", cause_by=action)

        # Add a message with a cause_by
        memory.add(message)

        # Delete the message
        memory.delete(message)
        assert message not in memory.storage
        assert message not in memory.index[action]

        # Try to delete the same message again (should not raise an error)
        memory.delete(message)
        assert message not in memory.storage
        assert message not in memory.index[action]

    def test_delete_without_cause_by(self):
        memory = Memory()
        message = Message(content="Hello")

        # Add a message without cause_by
        memory.add(message)

        # Delete the message
        memory.delete(message)
        assert message not in memory.storage

    def test_clear(self):
        memory = Memory()
        message = Message(content="Hello")
        memory.add(message)
        assert message in memory.storage
        memory.clear()
        assert len(memory.storage) == 0

    def test_count(self):
        memory = Memory()
        messages = [
            Message(content="Hello"),
            Message(content="Hi there"),
        ]
        memory.add_batch(messages)
        assert memory.count() == 2

    def test_try_remember(self):
        memory = Memory()
        messages = [
            Message(content="Hello"),
            Message(content="Hi there"),
        ]
        memory.add_batch(messages)
        assert len(memory.try_remember("Hi")) == 1

    def test_get(self):
        memory = Memory()
        messages = [
            Message(content="Message 1"),
            Message(content="Message 2"),
            Message(content="Message 3"),
        ]

        # Add messages
        memory.add_batch(messages)

        # Get the most recent message (k=1)
        recent_messages = memory.get(1)
        assert len(recent_messages) == 1
        assert recent_messages[0] == messages[-1]

        # Get the most recent two messages (k=2)
        recent_messages = memory.get(2)
        assert len(recent_messages) == 2
        assert recent_messages[0] == messages[-2]
        assert recent_messages[1] == messages[-1]

        # Get all messages (k=0)
        all_messages = memory.get(0)
        assert len(all_messages) == len(messages)
        assert all_messages == messages

        # Get more messages than available (k=10, only 3 messages available)
        more_messages = memory.get(10)
        assert len(more_messages) == len(messages)
        assert more_messages == messages

    def test_get_empty_memory(self):
        memory = Memory()

        # Get from an empty memory (k=1)
        recent_messages = memory.get(1)
        assert len(recent_messages) == 0

        # Get all from an empty memory (k=0)
        all_messages = memory.get(0)
        assert len(all_messages) == 0

    def test_get_by_action(self):
        memory = Memory()
        action = Action()
        message = Message(content="Hello", cause_by=action)
        memory.add(message)
        assert message in memory.get_by_action(action)

    def test_get_by_actions(self):
        memory = Memory()
        action1 = Action()
        action2 = Action()
        message1 = Message(content="Hello", cause_by=action1)
        message2 = Message(content="Hi there", cause_by=action2)
        memory.add(message1)
        memory.add(message2)
        actions = [action1, action2]
        assert len(memory.get_by_actions(actions)) == 2

    def test_remember(self):
        memory = Memory()
        m1, m2 = Message(content="Message 1"), Message(content="Message 2")
        m3, m4 = Message(content="Message 3"), Message(content="Message 4")
        messages = [m1, m2, m3]
        observed_messages = [m2, m3, m4]

        # Add messages to memory
        memory.add_batch(messages)

        # Remember the most recent observed message (k=1)
        remembered_messages = memory.remember(observed_messages, k=1)
        assert len(remembered_messages) == 2
        assert remembered_messages == [m2, m4]

        # Remember the two most recent observed messages (k=2)
        remembered_messages = memory.remember(observed_messages, k=2)
        assert len(remembered_messages) == 1
        assert remembered_messages == [m4]

        # Remember all observed messages (k=0)
        all_remembered_messages = memory.remember(observed_messages, k=0)
        assert len(all_remembered_messages) == 1
        assert all_remembered_messages == [m4]

    def test_remember_with_empty_memory(self):
        memory = Memory()
        observed_messages = [
            Message(content="Message 1"),
            Message(content="Message 2"),
        ]

        # Remember from an empty memory (k=1)
        remembered_messages = memory.remember(observed_messages, k=1)
        assert len(remembered_messages) == 2

        # Remember all from an empty memory (k=0)
        all_remembered_messages = memory.remember(observed_messages, k=0)
        assert len(all_remembered_messages) == 2
