import pytest

from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import AIMessage, LongTermMemoryItem, Message, UserMessage


class TestRoleZero:
    @pytest.fixture
    def mock_role_zero(self, mocker):
        role_zero = RoleZero()
        role_zero.rc.memory = mocker.Mock()
        role_zero.longterm_memory = mocker.Mock()
        return role_zero

    def test_get_all_memories(self, mocker, mock_role_zero: RoleZero):
        mock_memories = [Message(content="test1"), Message(content="test2")]
        mock_role_zero._fetch_memories = mocker.Mock(return_value=mock_memories)

        result = mock_role_zero._get_all_memories()

        assert result == mock_memories
        mock_role_zero._fetch_memories.assert_called_once_with(k=0)

    @pytest.mark.parametrize(
        "k,should_use_ltm,memories,related_memories,is_first_from_ai,expected",
        [
            (
                None,
                False,
                [UserMessage(content="user"), AIMessage(content="ai")],
                [],
                False,
                [UserMessage(content="user"), AIMessage(content="ai")],
            ),
            (
                1,
                True,
                [UserMessage(content="user")],
                [Message(content="related")],
                False,
                [Message(content="related"), UserMessage(content="user")],
            ),
            (
                None,
                True,
                [AIMessage(content="ai1"), UserMessage(content="user"), AIMessage(content="ai2")],
                [Message(content="related")],
                True,
                [Message(content="related"), UserMessage(content="user"), AIMessage(content="ai2")],
            ),
            (
                None,
                True,
                [UserMessage(content="user"), AIMessage(content="ai")],
                [Message(content="related")],
                False,
                [Message(content="related"), UserMessage(content="user"), AIMessage(content="ai")],
            ),
            (
                0,
                False,
                [UserMessage(content="user"), AIMessage(content="ai")],
                [],
                False,
                [UserMessage(content="user"), AIMessage(content="ai")],
            ),
        ],
    )
    def test_fetch_memories(
        self,
        mocker,
        mock_role_zero: RoleZero,
        k,
        should_use_ltm,
        memories,
        related_memories,
        is_first_from_ai,
        expected,
    ):
        mock_role_zero.memory_k = 2
        mock_role_zero.rc.memory.get = mocker.Mock(return_value=memories)
        mock_role_zero._should_use_longterm_memory = mocker.Mock(return_value=should_use_ltm)
        mock_role_zero.longterm_memory.fetch = mocker.Mock(return_value=related_memories)
        mock_role_zero._is_first_message_from_ai = mocker.Mock(return_value=is_first_from_ai)

        result = mock_role_zero._fetch_memories(k)

        assert len(result) == len(expected)
        for actual, expected_msg in zip(result, expected):
            assert actual.role == expected_msg.role
            assert actual.content == expected_msg.content

        really_k = k if k is not None else mock_role_zero.memory_k
        mock_role_zero.rc.memory.get.assert_called_once_with(really_k)

        if k != 0:
            mock_role_zero._should_use_longterm_memory.assert_called_once_with(k=really_k, k_memories=memories)

            if should_use_ltm:
                mock_role_zero.longterm_memory.fetch.assert_called_once_with(memories[-1].content)
                mock_role_zero._is_first_message_from_ai.assert_called_once_with(memories)

    def test_add_memory(self, mocker, mock_role_zero: RoleZero):
        message = AIMessage(content="ai")
        mock_role_zero.rc.memory.add = mocker.Mock()
        mock_role_zero._should_use_longterm_memory = mocker.Mock(return_value=True)
        mock_role_zero._transfer_to_longterm_memory = mocker.Mock()

        mock_role_zero._add_memory(message)

        mock_role_zero.rc.memory.add.assert_called_once_with(message)
        mock_role_zero._transfer_to_longterm_memory.assert_called_once()

    @pytest.mark.parametrize(
        "k,enable_longterm_memory,memory_count,k_memories,expected",
        [
            (0, True, 30, None, False),  # k is 0
            (None, False, 30, None, False),  # Long-term memory usage is disabled
            (None, True, 10, None, False),  # Memory count is less than or equal to memory_k
            (None, True, 30, [], False),  # k_memories is empty
            (None, True, 30, [AIMessage(content="ai")], False),  # Last message in k_memories is not a user message
            (None, True, 30, [AIMessage(content="ai"), UserMessage(content="user")], True),  # All conditions are met
        ],
    )
    def test_should_use_longterm_memory(
        self, mocker, mock_role_zero: RoleZero, k, enable_longterm_memory, memory_count, k_memories, expected
    ):
        mock_role_zero.enable_longterm_memory = enable_longterm_memory
        mock_role_zero.rc.memory.count = mocker.Mock(return_value=memory_count)
        mock_role_zero.memory_k = 20

        result = mock_role_zero._should_use_longterm_memory(k, k_memories)

        assert result == expected

    def test_transfer_to_longterm_memory(self, mocker, mock_role_zero: RoleZero):
        mock_item = LongTermMemoryItem(user_message=UserMessage(content="user"), ai_message=AIMessage(content="ai"))
        mock_role_zero._get_longterm_memory_item = mocker.Mock(return_value=mock_item)
        mock_role_zero.longterm_memory = mocker.Mock()

        mock_role_zero._transfer_to_longterm_memory()

        mock_role_zero.longterm_memory.add.assert_called_once_with(mock_item)

    def test_get_longterm_memory_item(self, mocker, mock_role_zero: RoleZero):
        mock_role_zero.memory_k = 2
        mock_messages = [
            UserMessage(content="user1"),
            AIMessage(content="ai1"),
            UserMessage(content="user2"),
            AIMessage(content="ai2"),
            UserMessage(content="user3"),  # memory_k + 2
            AIMessage(content="ai3"),  # memory_k + 1
            UserMessage(content="recent1"),
            AIMessage(content="recent2"),
        ]

        mock_role_zero.rc.memory.get_by_position = mocker.Mock(side_effect=lambda i: mock_messages[i])
        mock_role_zero.rc.memory.count = mocker.Mock(return_value=len(mock_messages))

        result = mock_role_zero._get_longterm_memory_item()

        assert isinstance(result, LongTermMemoryItem)
        assert result.user_message.content == "user3"
        assert result.ai_message.content == "ai3"

        mock_role_zero.rc.memory.get_by_position.assert_any_call(-(mock_role_zero.memory_k + 1))
        mock_role_zero.rc.memory.get_by_position.assert_any_call(-(mock_role_zero.memory_k + 2))

    @pytest.mark.parametrize(
        "memories,expected",
        [
            ([UserMessage(content="user")], True),
            ([AIMessage(content="ai")], False),
            ([], False),
        ],
    )
    def test_is_last_message_from_user(self, mock_role_zero: RoleZero, memories, expected):
        result = mock_role_zero._is_last_message_from_user(memories)
        assert result == expected

    @pytest.mark.parametrize(
        "memories,expected",
        [
            ([AIMessage(content="ai")], True),
            ([UserMessage(content="user")], False),
            ([], False),
        ],
    )
    def test_is_first_message_from_ai(self, mock_role_zero: RoleZero, memories, expected):
        result = mock_role_zero._is_first_message_from_ai(memories)
        assert result == expected
