import pytest

from metagpt.const import EXPERIENCE_MASK
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
        req = [{"content": "Original content 1"}]
        result = await context_builder.build(req=req)
        assert result == [{"content": "Updated content"}]

    def test_replace_example_content(self, context_builder, mocker):
        mocker.patch.object(RoleZeroContextBuilder, "fill_experience", return_value="Replaced content")
        result = context_builder.replace_example_content("Original text", "New example content")
        assert result == "Replaced content"
        context_builder.fill_experience.assert_called_once_with("Original text", "New example content")

    def test_fill_experience(self):
        text = f"Start\n# Past Experience\n{EXPERIENCE_MASK}\n\n# Instruction\nEnd"
        new_content = "New content"
        result = RoleZeroContextBuilder.fill_experience(text, new_content)
        expected = "Start\n# Past Experience\nNew content\n\n# Instruction\nEnd"
        assert result == expected

    def test_fill_experience_no_match(self):
        text = "Start\nNo markers\nEnd"
        new_content = "New content"
        result = RoleZeroContextBuilder.fill_experience(text, new_content)
        assert result == text
