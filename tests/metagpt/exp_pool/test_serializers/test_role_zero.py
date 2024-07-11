import json

import pytest

from metagpt.exp_pool.serializers import RoleZeroSerializer


class TestRoleZeroSerializer:
    @pytest.fixture
    def serializer(self):
        return RoleZeroSerializer()

    def test_serialize_req_empty_input(self, serializer: RoleZeroSerializer):
        assert serializer.serialize_req([]) == ""

    def test_serialize_req_with_content(self, serializer: RoleZeroSerializer):
        req = [
            {"content": "Command Editor.read executed: file_path=test.py"},
            {"content": "Some other content"},
            {
                "content": "# Data Structure\nsome data\n# Current Plan\nsome plan\n# Example\nsome example\n# Instruction\nsome instruction"
            },
        ]
        expected_output = json.dumps(
            [
                {"content": "Command Editor.read executed: file_path=test.py"},
                {
                    "content": "# Data Structure\n\n\n# Current Plan\nsome plan\n# Example\n\n\n# Instruction\nsome instruction"
                },
            ]
        )
        assert serializer.serialize_req(req) == expected_output

    def test_filter_req(self, serializer: RoleZeroSerializer):
        req = [
            {"content": "Command Editor.read executed: file_path=test1.py"},
            {"content": "Some other content"},
            {"content": "Command Editor.read executed: file_path=test2.py"},
            {"content": "Final content"},
        ]
        filtered_req = serializer._filter_req(req)
        assert len(filtered_req) == 3
        assert filtered_req[0]["content"] == "Command Editor.read executed: file_path=test1.py"
        assert filtered_req[1]["content"] == "Command Editor.read executed: file_path=test2.py"
        assert filtered_req[2]["content"] == "Final content"

    def test_clean_last_entry_content(self, serializer: RoleZeroSerializer):
        req = [
            {"content": "Some content"},
            {
                "content": "# Data Structure\nsome data\n# Current Plan\nsome plan\n# Example\nsome example\n# Instruction\nsome instruction"
            },
        ]
        serializer._clean_last_entry_content(req)
        expected_content = (
            "# Data Structure\n\n\n# Current Plan\nsome plan\n# Example\n\n\n# Instruction\nsome instruction"
        )
        assert req[-1]["content"] == expected_content

    def test_integration(self, serializer: RoleZeroSerializer):
        req = [
            {"content": "Command Editor.read executed: file_path=test.py"},
            {"content": "Some other content"},
            {
                "content": "# Data Structure\nsome data\n# Current Plan\nsome plan\n# Example\nsome example\n# Instruction\nsome instruction"
            },
        ]
        result = serializer.serialize_req(req)
        expected_output = json.dumps(
            [
                {"content": "Command Editor.read executed: file_path=test.py"},
                {
                    "content": "# Data Structure\n\n\n# Current Plan\nsome plan\n# Example\n\n\n# Instruction\nsome instruction"
                },
            ]
        )
        assert result == expected_output
