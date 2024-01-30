#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/19
@Author  : mashenquan
@File    : test_skill_loader.py
@Desc    : Unit tests.
"""
from pathlib import Path

import pytest

from metagpt.learn.skill_loader import SkillsDeclaration


@pytest.mark.asyncio
async def test_suite(context):
    context.kwargs.agent_skills = [
        {"id": 1, "name": "text_to_speech", "type": "builtin", "config": {}, "enabled": True},
        {"id": 2, "name": "text_to_image", "type": "builtin", "config": {}, "enabled": True},
        {"id": 3, "name": "ai_call", "type": "builtin", "config": {}, "enabled": True},
        {"id": 3, "name": "data_analysis", "type": "builtin", "config": {}, "enabled": True},
        {"id": 5, "name": "crawler", "type": "builtin", "config": {"engine": "ddg"}, "enabled": True},
        {"id": 6, "name": "knowledge", "type": "builtin", "config": {}, "enabled": True},
        {"id": 6, "name": "web_search", "type": "builtin", "config": {}, "enabled": True},
    ]
    pathname = Path(__file__).parent / "../../../docs/.well-known/skills.yaml"
    loader = await SkillsDeclaration.load(skill_yaml_file_name=pathname)
    skills = loader.get_skill_list(context=context)
    assert skills
    assert len(skills) >= 3
    for desc, name in skills.items():
        assert desc
        assert name

    entity = loader.entities.get("Assistant")
    assert entity
    assert entity.skills
    for sk in entity.skills:
        assert sk
        assert sk.arguments


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
