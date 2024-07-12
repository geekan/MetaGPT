import pytest

from metagpt.exp_pool.context_builders.base import BaseContextBuilder
from metagpt.exp_pool.context_builders.role_zero import RoleZeroContextBuilder


class TestRoleZeroContextBuilder:
    @pytest.fixture
    def context_builder(self):
        return RoleZeroContextBuilder()

    @pytest.mark.asyncio
    async def test_build_empty_req(self, context_builder):
        result = await context_builder.build(req=[])
        assert result == []

    @pytest.mark.asyncio
    async def test_build_no_experiences(self, context_builder, mocker):
        mocker.patch.object(BaseContextBuilder, "format_exps", return_value="")
        req = [{"content": "Original content"}]
        result = await context_builder.build(req=req)
        assert result == req

    @pytest.mark.asyncio
    async def test_build_with_experiences(self, context_builder, mocker):
        mocker.patch.object(BaseContextBuilder, "format_exps", return_value="Formatted experiences")
        mocker.patch.object(RoleZeroContextBuilder, "replace_example_content", return_value="Updated content")
        req = [{"content": "Original content 1"}, {"content": "Original content exp part"}]
        result = await context_builder.build(req=req)
        assert result == [{"content": "Updated content"}, {"content": "Original content exp part"}]

    def test_replace_example_content(self, context_builder, mocker):
        mocker.patch.object(RoleZeroContextBuilder, "replace_content_between_markers", return_value="Replaced content")
        result = context_builder.replace_example_content("Original text", "New example content")
        assert result == "Replaced content"
        context_builder.replace_content_between_markers.assert_called_once_with(
            "Original text", "# Example", "# Available Commands", "New example content"
        )

    def test_replace_content_between_markers(self):
        text = "Start\n# Example\nOld content\n# Available Commands\nEnd"
        new_content = "New content"
        result = RoleZeroContextBuilder.replace_content_between_markers(
            text, "# Example", "# Available Commands", new_content
        )
        expected = "Start\n# Example\nNew content\n\n# Available Commands\nEnd"
        assert result == expected

    def test_replace_content_between_markers_no_match(self):
        text = "Start\nNo markers\nEnd"
        new_content = "New content"
        result = RoleZeroContextBuilder.replace_content_between_markers(
            text, "# Example", "# Available Commands", new_content
        )
        assert result == text
