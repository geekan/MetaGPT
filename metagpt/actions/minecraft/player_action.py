# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 17:06
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.actions import Action
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from metagpt.document_store import FaissStore
from metagpt.const import CKPT_DIR

class PlayerActions(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.skills = {}
        self.qa_cache = {}
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
        # TODO: change to FaissStore
        # self.qa_cache_questions_vectordb = FaissStore( {CKPT_DIR}/ 'curriculum/vectordb'

    @classmethod
    def set_skills(cls, skills):
        cls.skills = skills
        # Check if Skill Manager's vectordb right using
        assert cls.vectordb._collection.count() == len(cls.skills), (
            f"Skill Manager's vectordb is not synced with skills.json.\n"
            f"There are {cls.vectordb._collection.count()} skills in vectordb but {len(cls.skills)} skills in skills.json.\n"
            f"Did you set resume=False when initializing the manager?\n"
            f"You may need to manually delete the vectordb directory for running from scratch."
        )

    @classmethod
    def set_qa_cache(cls, qa_cache):
        cls.qa_cache = qa_cache
        # Check if qa_cache right using
        # Check if Skill Manager's vectordb right using
        assert cls.qa_cache_questions_vectordb._collection.count() == len(
            cls.qa_cache
        ), (
            f"Curriculum Agent's qa cache question vectordb is not synced with qa_cache.json.\n"
            f"There are {cls.qa_cache_questions_vectordb._collection.count()} questions in vectordb "
            f"but {len(cls.qa_cache)} questions in qa_cache.json.\n"
            f"Did you set resume=False when initializing the agent?\n"
            f"You may need to manually delete the qa cache question vectordb directory for running from scratch.\n"
        )
    
    """Minecraft player info without any implementation details"""
    async def run(self, *args, **kwargs):
        raise NotImplementedError