# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 17:06
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import json

from metagpt.actions import Action
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

from metagpt.const import CKPT_DIR
from metagpt.config import CONFIG


class PlayerActions(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.skills = {}  # for skills.json
        self.qa_cache = {}
        self.check_init = True

        if (
            CONFIG.resume
        ):  # TODO: now for assert only, no update, cuz program using in step()
            with open(f"{CKPT_DIR}/skill/skills.json", "r") as f:
                self.skills = json.load(f)

            with open(f"{CKPT_DIR}/curriculum/qa_cache.json", "r") as f:
                self.qa_cache = json.load(f)

        self.retrieval_top_k = 5

        self.vectordb = Chroma(
            collection_name="skill_vectordb",
            embedding_function=OpenAIEmbeddings(),
            persist_directory=f"{CKPT_DIR}/skill/vectordb",
        )

        self.qa_cache_questions_vectordb = Chroma(
            collection_name="qa_cache_questions_vectordb",
            embedding_function=OpenAIEmbeddings(),
            persist_directory=f"{CKPT_DIR}/curriculum/vectordb",
        )

        # FIXME
        if self.check_init:
            # Check if Skill Manager's vectordb right using
            assert self.vectordb._collection.count() >= len(self.skills), (
                f"Skill Manager's vectordb is not synced with skills.json.\n"
                f"There are {self.vectordb._collection.count()} skills in vectordb but {len(self.skills)} skills in skills.json.\n"
                f"Did you set resume=False when initializing the manager?\n"
                f"You may need to manually delete the vectordb directory for running from scratch."
            )
            # Check if Skill Manager's vectordb right using
            assert self.qa_cache_questions_vectordb._collection.count() >= len(
                self.qa_cache
            ), (
                f"Curriculum Agent's qa cache question vectordb is not synced with qa_cache.json.\n"
                f"There are {self.qa_cache_questions_vectordb._collection.count()} questions in vectordb "
                f"but {len(self.qa_cache)} questions in qa_cache.json.\n"
                f"Did you set resume=False when initializing the agent?\n"
                f"You may need to manually delete the qa cache question vectordb directory for running from scratch.\n"
            )
            self.check_init = False
            # TODO: change to FaissStore
            # self.qa_cache_questions_vectordb = FaissStore( {CKPT_DIR}/ 'curriculum/vectordb'

    """Minecraft player info without any implementation details"""

    async def run(self, *args, **kwargs):
        raise NotImplementedError
