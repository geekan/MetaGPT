from datetime import datetime, timedelta

import pytest

from metagpt.actions import UserRequirement
from metagpt.const import TEAMLEADER_NAME
from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory
from metagpt.schema import AIMessage, LongTermMemoryItem, Message, UserMessage


class TestRoleZeroLongTermMemory:
    @pytest.fixture
    def mock_memory(self, mocker) -> RoleZeroLongTermMemory:
        memory = RoleZeroLongTermMemory()
        memory._resolve_rag_engine = mocker.Mock()
        return memory

    def test_add(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mock_memory._should_use_longterm_memory_for_add = mocker.Mock(return_value=True)
        mock_memory._transfer_to_longterm_memory = mocker.Mock()

        message = UserMessage(content="test")
        mock_memory.add(message)

        assert mock_memory.storage[-1] == message
        mock_memory._transfer_to_longterm_memory.assert_called_once()

    def test_get(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mock_memory._should_use_longterm_memory_for_get = mocker.Mock(return_value=True)
        mock_memory._build_longterm_memory_query = mocker.Mock(return_value="query")
        mock_memory._fetch_longterm_memories = mocker.Mock(return_value=[Message(content="long-term")])

        mock_memory.storage = [Message(content="short-term")]

        result = mock_memory.get()

        assert len(result) == 2
        assert result[0].content == "long-term"
        assert result[1].content == "short-term"

    def test_should_use_longterm_memory_for_add(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mocker.patch.object(mock_memory, "storage", [None] * 201)

        mock_memory.memory_k = 200

        assert mock_memory._should_use_longterm_memory_for_add() == True

        mocker.patch.object(mock_memory, "storage", [None] * 199)
        assert mock_memory._should_use_longterm_memory_for_add() == False

    @pytest.mark.parametrize(
        "k,is_last_from_user,count,expected",
        [
            (0, True, 201, False),
            (1, False, 201, False),
            (1, True, 199, False),
            (1, True, 201, True),
        ],
    )
    def test_should_use_longterm_memory_for_get(
        self, mocker, mock_memory: RoleZeroLongTermMemory, k, is_last_from_user, count, expected
    ):
        mock_memory._is_last_message_from_user_requirement = mocker.Mock(return_value=is_last_from_user)
        mocker.patch.object(mock_memory, "storage", [None] * count)
        mock_memory.memory_k = 200

        assert mock_memory._should_use_longterm_memory_for_get(k) == expected

    def test_transfer_to_longterm_memory(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mock_item = mocker.Mock()
        mock_memory._get_longterm_memory_item = mocker.Mock(return_value=mock_item)
        mock_memory._add_to_longterm_memory = mocker.Mock()

        mock_memory._transfer_to_longterm_memory()

        mock_memory._add_to_longterm_memory.assert_called_once_with(mock_item)

    def test_get_longterm_memory_item(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mock_message = Message(content="test")
        mock_memory.storage = [mock_message, mock_message]
        mock_memory.memory_k = 1

        result = mock_memory._get_longterm_memory_item()

        assert isinstance(result, LongTermMemoryItem)
        assert result.message == mock_message

    def test_add_to_longterm_memory(self, mock_memory: RoleZeroLongTermMemory):
        item = LongTermMemoryItem(message=Message(content="test"))
        mock_memory._add_to_longterm_memory(item)

        mock_memory.rag_engine.add_objs.assert_called_once_with([item])

    def test_build_longterm_memory_query(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mock_message = Message(content="query")
        mock_memory._get_the_last_message = mocker.Mock(return_value=mock_message)

        result = mock_memory._build_longterm_memory_query()

        assert result == "query"

    def test_get_the_last_message(self, mock_memory: RoleZeroLongTermMemory):
        mock_memory.storage = [Message(content="1"), Message(content="2")]

        result = mock_memory._get_the_last_message()

        assert result.content == "2"

    @pytest.mark.parametrize(
        "message,expected",
        [
            (UserMessage(content="test", cause_by=UserRequirement), True),
            (UserMessage(content="test", sent_from=TEAMLEADER_NAME), True),
            (UserMessage(content="test"), True),
            (AIMessage(content="test"), False),
            (None, False),
        ],
    )
    def test_is_last_message_from_user_requirement(
        self, mocker, mock_memory: RoleZeroLongTermMemory, message, expected
    ):
        mock_memory._get_the_last_message = mocker.Mock(return_value=message)

        assert mock_memory._is_last_message_from_user_requirement() == expected

    def test_fetch_longterm_memories(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mock_nodes = [mocker.Mock(), mocker.Mock()]
        mock_memory.rag_engine.retrieve = mocker.Mock(return_value=mock_nodes)
        mock_items = [
            LongTermMemoryItem(message=UserMessage(content="user1")),
            LongTermMemoryItem(message=AIMessage(content="ai1")),
        ]
        mock_memory._get_items_from_nodes = mocker.Mock(return_value=mock_items)

        result = mock_memory._fetch_longterm_memories("query")

        assert len(result) == 2
        assert result[0].content == "user1"
        assert result[1].content == "ai1"

    def test_get_items_from_nodes(self, mocker, mock_memory: RoleZeroLongTermMemory):
        now = datetime.now()
        mock_nodes = [
            mocker.Mock(
                metadata={
                    "obj": LongTermMemoryItem(
                        message=Message(content="2"), created_at=(now - timedelta(minutes=1)).timestamp()
                    )
                }
            ),
            mocker.Mock(
                metadata={
                    "obj": LongTermMemoryItem(
                        message=Message(content="1"), created_at=(now - timedelta(minutes=2)).timestamp()
                    )
                }
            ),
            mocker.Mock(metadata={"obj": LongTermMemoryItem(message=Message(content="3"), created_at=now.timestamp())}),
        ]

        result = mock_memory._get_items_from_nodes(mock_nodes)

        assert len(result) == 3
        assert [item.message.content for item in result] == ["1", "2", "3"]
