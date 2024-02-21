#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/6/5 01:44
# @Author  : alexanderwu
# @File    : skill_manager.py
# @Modified By: mashenquan, 2023/8/20. Remove useless `llm`

from metagpt.actions import Action
from metagpt.const import PROMPT_PATH
from metagpt.document_store.chromadb_store import ChromaStore
from metagpt.logs import logger

Skill = Action


class SkillManager:
    """Used to manage all skills.

    This class is responsible for adding, deleting, retrieving, and generating descriptions for skills.
    It interacts with a ChromaStore instance for storage and retrieval operations.

    Attributes:
        _store: An instance of ChromaStore used for storing skill information.
        _skills: A dictionary mapping skill names to Skill objects.
    """

    def __init__(self):
        """Initializes the SkillManager with a ChromaStore and an empty skill dictionary."""
        self._store = ChromaStore("skill_manager")
        self._skills: dict[str:Skill] = {}

    def add_skill(self, skill: Skill):
        """Adds a skill to the skill pool and searchable storage.

        Args:
            skill: The Skill object to be added.
        """
        self._skills[skill.name] = skill
        self._store.add(skill.desc, {"name": skill.name, "desc": skill.desc}, skill.name)

    def del_skill(self, skill_name: str):
        """Deletes a skill from the skill pool and searchable storage.

        Args:
            skill_name: The name of the skill to be deleted.
        """
        self._skills.pop(skill_name)
        self._store.delete(skill_name)

    def get_skill(self, skill_name: str) -> Skill:
        """Retrieves a specific skill by its name.

        Args:
            skill_name: The name of the skill to retrieve.

        Returns:
            The Skill object associated with the given name.
        """
        return self._skills.get(skill_name)

    def retrieve_skill(self, desc: str, n_results: int = 2) -> list[Skill]:
        """Obtains skills through the search engine based on a description.

        Args:
            desc: The description to search for.
            n_results: The number of results to return. Defaults to 2.

        Returns:
            A list of Skill objects that match the description.
        """
        return self._store.search(desc, n_results=n_results)["ids"][0]

    def retrieve_skill_scored(self, desc: str, n_results: int = 2) -> dict:
        """Obtains skills and their scores through the search engine based on a description.

        Args:
            desc: The description to search for.
            n_results: The number of results to return. Defaults to 2.

        Returns:
            A dictionary consisting of skills and their scores.
        """
        return self._store.search(desc, n_results=n_results)

    def generate_skill_desc(self, skill: Skill) -> str:
        """Generates descriptive text for a given skill.

        Args:
            skill: The Skill object for which to generate a description.

        Returns:
            A string containing the generated description.
        """
        path = PROMPT_PATH / "generate_skill.md"
        text = path.read_text()
        logger.info(text)


if __name__ == "__main__":
    manager = SkillManager()
    manager.generate_skill_desc(Action())
