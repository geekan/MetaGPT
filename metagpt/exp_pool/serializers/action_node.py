"""ActionNode Serializer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

# Import ActionNode only for type checking to avoid circular imports
if TYPE_CHECKING:
    from metagpt.actions.action_node import ActionNode

from metagpt.exp_pool.serializers.simple import SimpleSerializer


class ActionNodeSerializer(SimpleSerializer):
    def serialize_resp(self, resp: ActionNode) -> str:
        return resp.instruct_content.model_dump_json()

    def deserialize_resp(self, resp: str) -> ActionNode:
        """Customized deserialization, it will be triggered when a perfect experience is found.

        ActionNode cannot be serialized, it throws an error 'cannot pickle 'SSLContext' object'.
        """

        class InstructContent:
            def __init__(self, json_data):
                self.json_data = json_data

            def model_dump_json(self):
                return self.json_data

        from metagpt.actions.action_node import ActionNode

        action_node = ActionNode(key="", expected_type=Type[str], instruction="", example="")
        action_node.instruct_content = InstructContent(resp)

        return action_node
