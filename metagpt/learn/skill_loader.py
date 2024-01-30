#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/8/18
# @Author  : mashenquan
# @File    : skill_loader.py
# @Desc    : Skill YAML Configuration Loader.

from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import yaml
from pydantic import BaseModel, Field

from metagpt.context import Context


class Example(BaseModel):
    """Represents an example of a skill's usage.

    Attributes:
        ask: The question or input given to the skill.
        answer: The expected answer or output from the skill.
    """

    ask: str
    answer: str


class Returns(BaseModel):
    """Defines the return type and format of a skill's response.

    Attributes:
        type: The data type of the return value.
        format: The format of the return value, if applicable.
    """

    type: str
    format: Optional[str] = None


class Parameter(BaseModel):
    """Describes a parameter for a skill.

    Attributes:
        type: The data type of the parameter.
        description: A brief description of the parameter.
    """

    type: str
    description: str = None


class Skill(BaseModel):
    """Represents a skill, including its metadata and behavior.

    Attributes:
        name: The name of the skill.
        description: A brief description of the skill.
        id: An optional unique identifier for the skill.
        x_prerequisite: A dictionary of prerequisites for the skill.
        parameters: A dictionary of parameters the skill accepts.
        examples: A list of examples demonstrating the skill's usage.
        returns: The expected return type and format of the skill's response.
    """

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
    """Represents an entity that groups multiple skills.

    Attributes:
        name: The name of the entity.
        skills: A list of skills associated with the entity.
    """

    name: str = None
    skills: List[Skill]


class Components(BaseModel):
    """Placeholder for future expansion, currently empty."""

    pass


class SkillsDeclaration(BaseModel):
    """Represents the entire skill declaration, including entities and components.

    Attributes:
        skillapi: The version of the skill API.
        entities: A dictionary of entities, each containing a list of skills.
        components: Optional components for additional configurations.
    """

    skillapi: str
    entities: Dict[str, Entity]
    components: Components = None

    @staticmethod
    async def load(skill_yaml_file_name: Path = None) -> "SkillsDeclaration":
        """Loads the skills declaration from a YAML file.

        Args:
            skill_yaml_file_name: The path to the YAML file containing the skills declaration.

        Returns:
            An instance of SkillsDeclaration populated with the data from the YAML file.
        """
        if not skill_yaml_file_name:
            skill_yaml_file_name = Path(__file__).parent.parent.parent / "docs/.well-known/skills.yaml"
        async with aiofiles.open(str(skill_yaml_file_name), mode="r") as reader:
            data = await reader.read(-1)
        skill_data = yaml.safe_load(data)
        return SkillsDeclaration(**skill_data)

    def get_skill_list(self, entity_name: str = "Assistant", context: Context = None) -> Dict:
        """Return the skill name based on the skill description.

        Args:
            entity_name: The name of the entity to retrieve skills for.
            context: Optional; the context within which to evaluate the skills.

        Returns:
            A dictionary mapping skill descriptions to skill names.
        """
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
        """Return a skill by name.

        Args:
            name: The name of the skill to retrieve.
            entity_name: The name of the entity to which the skill belongs.

        Returns:
            The Skill object if found, None otherwise.
        """
        entity = self.entities.get(entity_name)
        if not entity:
            return None
        for sk in entity.skills:
            if sk.name == name:
                return sk
