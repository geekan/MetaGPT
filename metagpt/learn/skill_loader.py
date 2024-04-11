#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : skill_loader.py
@Desc    : Skill YAML Configuration Loader.
"""
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from metagpt.context import Context
from metagpt.utils.common import aread


class Example(BaseModel):
    ask: str
    answer: str


class Returns(BaseModel):
    type: str
    format: Optional[str] = None


class Parameter(BaseModel):
    type: str
    description: str = None


class Skill(BaseModel):
    name: str
    description: str = None
    id: str = None
    x_prerequisite: Dict = Field(default=None, alias="x-prerequisite")
    parameters: Dict[str, Parameter] = None
    examples: List[Example]
    returns: Returns

    @property
    def arguments(self) -> Dict:
        if not self.parameters:
            return {}
        ret = {}
        for k, v in self.parameters.items():
            ret[k] = v.description if v.description else ""
        return ret


class Entity(BaseModel):
    name: str = None
    skills: List[Skill]


class Components(BaseModel):
    pass


class SkillsDeclaration(BaseModel):
    skillapi: str
    entities: Dict[str, Entity]
    components: Components = None

    @staticmethod
    async def load(skill_yaml_file_name: Path = None) -> "SkillsDeclaration":
        if not skill_yaml_file_name:
            skill_yaml_file_name = Path(__file__).parent.parent.parent / "docs/.well-known/skills.yaml"
        data = await aread(filename=skill_yaml_file_name)
        skill_data = yaml.safe_load(data)
        return SkillsDeclaration(**skill_data)

    def get_skill_list(self, entity_name: str = "Assistant", context: Context = None) -> Dict:
        """Return the skill name based on the skill description."""
        entity = self.entities.get(entity_name)
        if not entity:
            return {}

        # List of skills that the agent chooses to activate.
        ctx = context or Context()
        agent_skills = ctx.kwargs.agent_skills
        if not agent_skills:
            return {}

        class _AgentSkill(BaseModel):
            name: str

        names = [_AgentSkill(**i).name for i in agent_skills]
        return {s.description: s.name for s in entity.skills if s.name in names}

    def get_skill(self, name, entity_name: str = "Assistant") -> Skill:
        """Return a skill by name."""
        entity = self.entities.get(entity_name)
        if not entity:
            return None
        for sk in entity.skills:
            if sk.name == name:
                return sk
