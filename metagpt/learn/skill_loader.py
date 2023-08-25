from pathlib import Path
from typing import List, Dict

import yaml
from pydantic import BaseModel


class Skill(BaseModel):
    name: str
    description: str
    requisite: List[str]


class EntitySkills(BaseModel):
    skills: List[Skill]


class SkillsDeclaration(BaseModel):
    entities: Dict[str, EntitySkills]


class SkillLoader:
    def __init__(self):
        skill_file_name = Path(__file__).parent.parent.parent / ".well-known/skills.yaml"
        with open(str(skill_file_name), 'r') as file:
            skills = yaml.safe_load(file)
        self._skills = SkillsDeclaration(**skills)

    def get_skill_list(self, entity_name: str = "Assistant"):
        if not self._skills or entity_name not in self._skills.entities:
            return {}
        entity_skills = self._skills.entities.get(entity_name)

        description_to_name_mappings = {}
        for s in entity_skills.skills:
            description_to_name_mappings[s.description] = s.name

        return description_to_name_mappings
