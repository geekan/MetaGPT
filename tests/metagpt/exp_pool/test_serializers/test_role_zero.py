import json

import pytest

from metagpt.exp_pool.serializers import RoleZeroSerializer


class TestRoleZeroSerializer:
    @pytest.fixture
    def serializer(self) -> RoleZeroSerializer:
        return RoleZeroSerializer()

    @pytest.fixture
    def last_item(self) -> dict:
        return {
            "role": "user",
            "content": "# Current Plan\nsome plan\n# Current Plan\nsome plan\n# Instruction\nsome instruction",
        }

    @pytest.fixture
    def sample_req(self):
        return [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    def test_serialize_req_empty_input(self, serializer: RoleZeroSerializer):
        assert serializer.serialize_req(req=[]) == ""

    def test_serialize_req_with_content(self, serializer: RoleZeroSerializer, last_item: dict):
        req = [
            {"role": "user", "content": "Command Editor.read executed: file_path=test.py"},
            {"role": "assistant", "content": "Some other content"},
            last_item,
        ]
        expected_output = json.dumps([{"role": "user", "content": "Command Editor.read executed: file_path=test.py"}])
        assert serializer.serialize_req(req=req) == expected_output

    def test_filter_req(self, serializer: RoleZeroSerializer):
        req = [
            {"role": "user", "content": "Command Editor.read executed: file_path=test1.py"},
            {"role": "assistant", "content": "Some other content"},
            {"role": "user", "content": "Command Editor.read executed: file_path=test2.py"},
            {"role": "assistant", "content": "Final content"},
        ]
        filtered_req = serializer._filter_req(req)
        assert len(filtered_req) == 2
        assert filtered_req[0]["content"] == "Command Editor.read executed: file_path=test1.py"
        assert filtered_req[1]["content"] == "Command Editor.read executed: file_path=test2.py"
