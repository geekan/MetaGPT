from typing import Type

import pytest

from metagpt.actions.action_node import ActionNode
from metagpt.exp_pool.serializers.action_node import ActionNodeSerializer


class TestActionNodeSerializer:
    @pytest.fixture
    def serializer(self):
        return ActionNodeSerializer()

    @pytest.fixture
    def action_node(self):
        class InstructContent:
            def __init__(self, json_data):
                self.json_data = json_data

            def model_dump_json(self):
                return self.json_data

        action_node = ActionNode(key="", expected_type=Type[str], instruction="", example="")
        action_node.instruct_content = InstructContent('{"key": "value"}')

        return action_node

    def test_serialize_resp(self, serializer: ActionNodeSerializer, action_node: ActionNode):
        serialized = serializer.serialize_resp(action_node)
        assert serialized == '{"key": "value"}'

    def test_deserialize_resp(self, serializer: ActionNodeSerializer):
        deserialized = serializer.deserialize_resp('{"key": "value"}')
        assert isinstance(deserialized, ActionNode)
        assert deserialized.instruct_content.model_dump_json() == '{"key": "value"}'
