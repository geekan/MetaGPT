from pathlib import Path
from typing import List, Dict, Optional

import yaml
from pydantic import BaseModel


class Example(BaseModel):
    ask: str
    answer: str

class Returns(BaseModel):
    type: str
    format: Optional[str] = None

class Skill(BaseModel):
    name: str
    description: str
    id: str
    requisite: List[str]
    arguments: Dict
    examples: List[Example]
    returns: Returns


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

    def get_skill_list(self, entity_name: str = "Assistant") -> Dict:
        entity_skills = self.get_entity(entity_name)
        if not entity_skills:
            return {}

        description_to_name_mappings = {}
        for s in entity_skills.skills:
            description_to_name_mappings[s.description] = s.name

        return description_to_name_mappings

    def get_skill(self, name, entity_name: str = "Assistant") -> Skill:
        entity = self.get_entity(entity_name)
        if not entity:
            return None
        for sk in entity.skills:
            if sk.name == name:
                return sk

    def get_entity(self, name) -> EntitySkills:
        if not self._skills:
            return None
        return self._skills.entities.get(name)