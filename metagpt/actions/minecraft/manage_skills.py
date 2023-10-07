# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:56
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import os
import json

from metagpt.logs import logger
from metagpt.actions.minecraft.player_action import PlayerActions as Action
from metagpt.const import CKPT_DIR


class RetrieveSkills(Action):
    """
    Action class for retrieving skills.
    Refer to the code in the voyager/agents/skill.py for implementation details.
    """

    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.llm.model = "gpt-3.5-turbo"

    async def run(self, query, skills, *args, **kwargs):
        # Implement the logic for retrieving skills here.
        k = min(self.vectordb._collection.count(), self.retrieval_top_k)
        if k == 0:
            return []
        logger.info(f"Skill Manager retrieving for {k} skills")
        docs_and_scores = self.vectordb.similarity_search_with_score(query, k=k)
        logger.info(
            f"Skill Manager retrieved skills: "
            f"{', '.join([doc.metadata['name'] for doc, _ in docs_and_scores])}"
        )
        retrieve_skills = []
        for doc, _ in docs_and_scores:
            retrieve_skills.append(skills[doc.metadata["name"]]["code"])
        return retrieve_skills


class AddNewSkills(Action):
    """
    Action class for adding new skills.
    Refer to the code in the voyager/agents/skill.py for implementation details.
    """

    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.llm.model = "gpt-3.5-turbo"

    async def run(
        self, task, program_name, program_code, skills, skill_desp, *args, **kwargs
    ):
        # Implement the logic for adding new skills here.
        # TODO: Fix this
        logger.info(f"check task {task}")
        if task.startswith("Deposit useless items into the chest at"):
            # No need to reuse the deposit skill
            return {}
        logger.info(
            f"Skill Manager generated description for {program_name}:\n{skill_desp}\033[0m"
        )
        logger.info(f"check skills {skills}")
        
        if program_name in skills:
            logger.info(f"Skill {program_name} already exists. Rewriting!")
            self.vectordb._collection.delete(ids=[program_name])
            i = 2
            while f"{program_name}V{i}.js" in os.listdir(f"{CKPT_DIR}/skill/code"):
                i += 1
            dumped_program_name = f"{program_name}V{i}"
        else:
            dumped_program_name = program_name
        self.vectordb.add_texts(
            texts=[skill_desp],
            ids=[program_name],
            metadatas=[{"name": program_name}],
        )

        # FIXME
        # assert self.vectordb._collection.count() == len(
        #     skills
        # ), "vectordb is not synced with skills.json"

        with open(f"{CKPT_DIR}/skill/code/{dumped_program_name}.js", "w") as f:
            f.write(program_code)
        with open(f"{CKPT_DIR}/skill/description/{dumped_program_name}.txt", "w") as f:
            f.write(skill_desp)
        with open(f"{CKPT_DIR}/skill/skills.json", "w") as f:
            json.dump(skills, f)
        self.vectordb.persist()
        return {
            "code": program_code,
            "description": skill_desp,
        }


class GenerateSkillDescription(Action):
    """
    Action class for generating skill descriptions.
    Refer to the code in the voyager/agents/skill.py for implementation details.
    """

    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.llm.model = "gpt-3.5-turbo"

    async def run(self, program_name, human_message, system_message, *args, **kwargs):
        # Implement the logic for generating skill descriptions here.
        rsp = await self._aask(prompt=human_message, system_msgs=system_message)
        skill_description = f"    // { rsp}"
        return f"async function {program_name}(bot) {{\n{skill_description}\n}}"
