import glob
import json
import os
from typing import Optional

import chromadb
from chromadb import Collection
from chromadb.utils import embedding_functions
from pydantic import model_validator

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.ext.werewolf.schema import RoleExperience
from metagpt.logs import logger

DEFAULT_COLLECTION_NAME = "role_reflection"  # FIXME: some hard code for now
EMB_FN = embedding_functions.OpenAIEmbeddingFunction(
    api_key=config.llm.api_key,
    api_base=config.llm.base_url,
    api_type=config.llm.api_type,
    model_name="text-embedding-ada-002",
)


class AddNewExperiences(Action):
    name: str = "AddNewExperience"
    collection_name: str = DEFAULT_COLLECTION_NAME
    delete_existing: bool = False
    collection: Optional[Collection] = None

    @model_validator(mode="after")
    def validate_collection(self):
        if self.collection:
            return

        chroma_client = chromadb.PersistentClient(path=f"{DEFAULT_WORKSPACE_ROOT}/werewolf_game/chroma")
        if self.delete_existing:
            try:
                chroma_client.get_collection(name=self.collection_name)
                chroma_client.delete_collection(name=self.collection_name)
                logger.info(f"existing collection {self.collection_name} deleted")
            except:
                pass

        self.collection = chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=EMB_FN,
        )

    def run(self, experiences: list[RoleExperience]):
        if not experiences:
            return
        for i, exp in enumerate(experiences):
            exp.id = f"{exp.profile}-{exp.name}-step{i}-round_{exp.round_id}"
        ids = [exp.id for exp in experiences]
        documents = [exp.reflection for exp in experiences]
        metadatas = [exp.model_dump() for exp in experiences]

        AddNewExperiences._record_experiences_local(experiences)

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def add_from_file(self, file_path):
        with open(file_path, "r") as fl:
            lines = fl.readlines()
        experiences = [RoleExperience.model_validate_json(line) for line in lines]
        experiences = [exp for exp in experiences if len(exp.reflection) > 2]  # not "" or not '""'

        ids = [exp.id for exp in experiences]
        documents = [exp.reflection for exp in experiences]
        metadatas = [exp.model_dump() for exp in experiences]

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    @staticmethod
    def _record_experiences_local(experiences: list[RoleExperience]):
        round_id = experiences[0].round_id
        version = experiences[0].version
        version = "test" if not version else version
        experiences = [exp.model_dump_json() for exp in experiences]
        experience_folder = DEFAULT_WORKSPACE_ROOT / f"werewolf_game/experiences/{version}"
        if not os.path.exists(experience_folder):
            os.makedirs(experience_folder)
        save_path = f"{experience_folder}/{round_id}.json"
        with open(save_path, "a") as fl:
            fl.write("\n".join(experiences))
            fl.write("\n")
        logger.info(f"experiences saved to {save_path}")


class RetrieveExperiences(Action):
    name: str = "RetrieveExperiences"
    collection_name: str = DEFAULT_COLLECTION_NAME
    has_experiences: bool = True
    collection: Optional[Collection] = None

    @model_validator(mode="after")
    def validate_collection(self):
        if self.collection:
            return
        chroma_client = chromadb.PersistentClient(path=f"{DEFAULT_WORKSPACE_ROOT}/werewolf_game/chroma")
        try:
            self.collection = chroma_client.get_collection(
                name=self.collection_name,
                embedding_function=EMB_FN,
            )
            self.has_experiences = True
        except:
            logger.warning(f"No experience pool {self.collection_name}")
            self.has_experiences = False

    def run(self, query: str, profile: str, topk: int = 5, excluded_version: str = "", verbose: bool = False) -> str:
        """_summary_

        Args:
            query (str): 用当前的reflection作为query去检索过去相似的reflection
            profile (str): _description_
            topk (int, optional): _description_. Defaults to 5.

        Returns:
            _type_: _description_
        """
        if not self.has_experiences or len(query) <= 2:  # not "" or not '""'
            return ""

        filters = {"profile": profile}
        ### 消融实验逻辑 ###
        if profile == "Werewolf":  # 狼人作为基线，不用经验
            logger.warning("Disable werewolves' experiences")
            return ""
        if excluded_version:
            filters = {"$and": [{"profile": profile}, {"version": {"$ne": excluded_version}}]}  # 不用同一版本的经验，只用之前的
        #################

        results = self.collection.query(
            query_texts=[query],
            n_results=topk,
            where=filters,
        )

        logger.info(f"retrieve {profile}'s experiences")
        past_experiences = [RoleExperience(**res) for res in results["metadatas"][0]]
        if verbose:
            logger.info("past_experiences: {}".format("\n\n".join(past_experiences)))
            distances = results["distances"][0]
            logger.info(f"distances: {distances}")

        template = """
        {
            "Situation __i__": "__situation__"
            ,"Moderator's instruction": "__instruction__"
            ,"Your action or speech during that time": "__response__"
            ,"Reality": "In fact, it turned out the true roles are __game_step__",
            ,"Outcome": "You __outcome__ in the end"
        }
        """
        past_experiences = [
            (
                template.replace("__i__", str(i))
                .replace("__situation__", exp.reflection)
                .replace("__instruction__", exp.instruction)
                .replace("__response__", exp.response)
                .replace("__game_step__", exp.game_setup.replace("0 | Game setup:\n", "").replace("\n", " "))
                .replace("__outcome__", exp.outcome)
            )
            for i, exp in enumerate(past_experiences)
        ]
        logger.info("past_experiences: {}".format("\n".join(past_experiences)))
        logger.info("retrieval done")

        return json.dumps(past_experiences)


# FIXME: below are some utility functions, should be moved to appropriate places
def delete_collection(name):
    chroma_client = chromadb.PersistentClient(path=f"{DEFAULT_WORKSPACE_ROOT}/werewolf_game/chroma")
    chroma_client.delete_collection(name=name)


def add_file_batch(folder, **kwargs):
    action = AddNewExperiences(**kwargs)
    file_paths = glob.glob(str(folder) + "/*")
    for fp in file_paths:
        logger.info(f"file_path: {fp}")
        action.add_from_file(fp)


def modify_collection():
    chroma_client = chromadb.PersistentClient(path=f"{DEFAULT_WORKSPACE_ROOT}/werewolf_game/chroma")
    collection = chroma_client.get_collection(name=DEFAULT_COLLECTION_NAME)
    updated_name = DEFAULT_COLLECTION_NAME + "_backup"
    collection.modify(name=updated_name)
    try:
        chroma_client.get_collection(name=DEFAULT_COLLECTION_NAME)
    except:
        logger.info(f"collection {DEFAULT_COLLECTION_NAME} not found")
    updated_collection = chroma_client.get_collection(name=updated_name)
    logger.info(f"updated_collection top5 documents {updated_collection.get()['documents'][-5:]}")
