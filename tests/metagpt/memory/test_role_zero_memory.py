from datetime import datetime, timedelta

import pytest

from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory
from metagpt.schema import AIMessage, LongTermMemoryItem, UserMessage


class TestRoleZeroLongTermMemory:
    @pytest.fixture
    def mock_memory(self, mocker) -> RoleZeroLongTermMemory:
        memory = RoleZeroLongTermMemory()
        memory._resolve_rag_engine = mocker.Mock()
        return memory

    def test_fetch_empty_query(self, mock_memory: RoleZeroLongTermMemory):
        assert mock_memory.fetch("") == []

    def test_fetch(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mock_node1 = mocker.Mock()
        mock_node2 = mocker.Mock()
        mock_node1.metadata = {
            "obj": LongTermMemoryItem(user_message=UserMessage(content="user1"), ai_message=AIMessage(content="ai1"))
        }
        mock_node2.metadata = {
            "obj": LongTermMemoryItem(user_message=UserMessage(content="user2"), ai_message=AIMessage(content="ai2"))
        }

        mock_memory.rag_engine.retrieve.return_value = [mock_node1, mock_node2]

        result = mock_memory.fetch("test query")

        assert len(result) == 4
        assert isinstance(result[0], UserMessage)
        assert isinstance(result[1], AIMessage)
        assert result[0].content == "user1"
        assert result[1].content == "ai1"
        assert result[2].content == "user2"
        assert result[3].content == "ai2"

        mock_memory.rag_engine.retrieve.assert_called_once_with("test query")

    def test_add_empty_item(self, mock_memory: RoleZeroLongTermMemory):
        mock_memory.add(None)
        mock_memory.rag_engine.add_objs.assert_not_called()

    def test_add_item(self, mock_memory: RoleZeroLongTermMemory):
        item = LongTermMemoryItem(user_message=UserMessage(content="user"), ai_message=AIMessage(content="ai"))
        mock_memory.add(item)
        mock_memory.rag_engine.add_objs.assert_called_once_with([item])

    def test_get_items_from_nodes(self, mocker, mock_memory: RoleZeroLongTermMemory):
        mock_node1 = mocker.Mock()
        mock_node2 = mocker.Mock()
        mock_node3 = mocker.Mock()

        now = datetime.now()
        item1 = LongTermMemoryItem(
            user_message=UserMessage(content="user1"), ai_message=AIMessage(content="ai1"), created_at=now.timestamp()
        )
        item2 = LongTermMemoryItem(
            user_message=UserMessage(content="user2"),
            ai_message=AIMessage(content="ai2"),
            created_at=(now - timedelta(minutes=5)).timestamp(),
        )
        item3 = LongTermMemoryItem(
            user_message=UserMessage(content="user3"),
            ai_message=AIMessage(content="ai3"),
            created_at=(now + timedelta(minutes=5)).timestamp(),
        )

        mock_node1.metadata = {"obj": item1}
        mock_node2.metadata = {"obj": item2}
        mock_node3.metadata = {"obj": item3}

        result = mock_memory._get_items_from_nodes([mock_node1, mock_node2, mock_node3])

        assert len(result) == 3
        assert result[0] == item2
        assert result[1] == item1
        assert result[2] == item3
        assert [item.user_message.content for item in result] == ["user2", "user1", "user3"]
        assert [item.ai_message.content for item in result] == ["ai2", "ai1", "ai3"]
