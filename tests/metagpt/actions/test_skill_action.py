#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/19
@Author  : mashenquan
@File    : test_skill_action.py
@Desc    : Unit tests.
"""
import pytest

from metagpt.actions.skill_action import ArgumentsParingAction, SkillAction
from metagpt.learn.skill_loader import Example, Parameter, Returns, Skill


class TestSkillAction:
    skill = Skill(
        name="text_to_image",
        description="Create a drawing based on the text.",
        id="text_to_image.text_to_image",
        x_prerequisite={
            "configurations": {
                "OPENAI_API_KEY": {
                    "type": "string",
                    "description": "OpenAI API key, For more details, checkout: `https://platform.openai.com/account/api-keys`",
                },
                "metagpt_tti_url": {"type": "string", "description": "Model url."},
            },
            "required": {"oneOf": ["OPENAI_API_KEY", "metagpt_tti_url"]},
        },
        parameters={
            "text": Parameter(type="string", description="The text used for image conversion."),
            "size_type": Parameter(type="string", description="size type"),
        },
        examples=[
            Example(ask="Draw a girl", answer='text_to_image(text="Draw a girl", size_type="512x512")'),
            Example(ask="Draw an apple", answer='text_to_image(text="Draw an apple", size_type="512x512")'),
        ],
        returns=Returns(type="string", format="base64"),
    )

    @pytest.mark.asyncio
    async def test_parser(self):
        args = ArgumentsParingAction.parse_arguments(
            skill_name="text_to_image", txt='`text_to_image(text="Draw an apple", size_type="512x512")`'
        )
        assert args.get("text") == "Draw an apple"
        assert args.get("size_type") == "512x512"

    @pytest.mark.asyncio
    async def test_parser_action(self, mocker, context):
        # mock
        mocker.patch("metagpt.learn.text_to_image", return_value="https://mock.com/xxx")

        parser_action = ArgumentsParingAction(skill=self.skill, ask="Draw an apple", context=context)
        rsp = await parser_action.run()
        assert rsp
        assert parser_action.args
        assert parser_action.args.get("text") == "Draw an apple"
        assert parser_action.args.get("size_type") == "512x512"

        action = SkillAction(skill=self.skill, args=parser_action.args, context=context)
        rsp = await action.run()
        assert rsp
        assert "image/png;base64," in rsp.content or "http" in rsp.content

    @pytest.mark.parametrize(
        ("skill_name", "txt", "want"),
        [
            ("skill1", 'skill1(a="1", b="2")', {"a": "1", "b": "2"}),
            ("skill1", '(a="1", b="2")', None),
            ("skill1", 'skill1(a="1", b="2"', None),
        ],
    )
    def test_parse_arguments(self, skill_name, txt, want):
        args = ArgumentsParingAction.parse_arguments(skill_name, txt)
        assert args == want

    @pytest.mark.asyncio
    async def test_find_and_call_function_error(self):
        with pytest.raises(ValueError):
            await SkillAction.find_and_call_function("dummy_call", {"a": 1})

    @pytest.mark.asyncio
    async def test_skill_action_error(self, context):
        action = SkillAction(skill=self.skill, args={}, context=context)
        rsp = await action.run()
        assert "Error" in rsp.content


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
