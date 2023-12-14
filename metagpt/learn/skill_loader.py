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

from metagpt.config import CONFIG


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


class SkillLoader:
    def __init__(self, skill_yaml_file_name: Path = None):
        if not skill_yaml_file_name:
            skill_yaml_file_name = Path(__file__).parent.parent.parent / ".well-known/skills.yaml"
        with open(str(skill_yaml_file_name), "r") as file:
            skills = yaml.safe_load(file)
        self._skills = SkillsDeclaration(**skills)

    def get_skill_list(self, entity_name: str = "Assistant") -> Dict:
        """Return the skill name based on the skill description."""
        entity = self.get_entity(entity_name)
        if not entity:
            return {}

        agent_skills = CONFIG.agent_skills
        if not agent_skills:
            return {}

        class AgentSkill(BaseModel):
            name: str

        names = [AgentSkill(**i).name for i in agent_skills]
        description_to_name_mappings = {}
        for s in entity.skills:
            if s.name not in names:
                continue
            description_to_name_mappings[s.description] = s.name

        return description_to_name_mappings

    def get_skill(self, name, entity_name: str = "Assistant") -> Skill:
        """Return a skill by name."""
        entity = self.get_entity(entity_name)
        if not entity:
            return None
        for sk in entity.skills:
            if sk.name == name:
                return sk

    def get_entity(self, name) -> Entity:
        """Return a list of skills for the entity."""
        if not self._skills:
            return None
        return self._skills.entities.get(name)


if __name__ == "__main__":
    CONFIG.agent_skills = [
        {"id": 1, "name": "text_to_speech", "type": "builtin", "config": {}, "enabled": True},
        {"id": 2, "name": "text_to_image", "type": "builtin", "config": {}, "enabled": True},
        {"id": 3, "name": "ai_call", "type": "builtin", "config": {}, "enabled": True},
        {"id": 3, "name": "data_analysis", "type": "builtin", "config": {}, "enabled": True},
        {"id": 5, "name": "crawler", "type": "builtin", "config": {"engine": "ddg"}, "enabled": True},
        {"id": 6, "name": "knowledge", "type": "builtin", "config": {}, "enabled": True},
    ]
    loader = SkillLoader()
    print(loader.get_skill_list())
