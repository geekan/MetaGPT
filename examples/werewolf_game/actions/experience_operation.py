import json
import os
import glob

import chromadb
from chromadb.utils import embedding_functions

from metagpt.config import CONFIG
from metagpt.actions import Action
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from examples.werewolf_game.schema import RoleExperience

DEFAULT_COLLECTION_NAME = "role_reflection" # FIXME: some hard code for now
EMB_FN = embedding_functions.OpenAIEmbeddingFunction(
    api_key=CONFIG.openai_api_key,
    api_base=CONFIG.openai_api_base,
    api_type=CONFIG.openai_api_type,
    model_name="text-embedding-ada-002",
    api_version="2",
)

class AddNewExperiences(Action):
    def __init__(
        self, name="AddNewExperience", context=None, llm=None,
        collection_name=DEFAULT_COLLECTION_NAME, delete_existing=False,
    ):
        super().__init__(name, context, llm)
        chroma_client = chromadb.PersistentClient(path=f"{WORKSPACE_ROOT}/werewolf_game/chroma")
        if delete_existing:
            try:
                chroma_client.get_collection(name=collection_name)
                chroma_client.delete_collection(name=collection_name)
                logger.info(f"existing collection {collection_name} deleted")
            except:
                pass

        # emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="multi-qa-mpnet-base-cos-v1")

        self.collection = chroma_client.get_or_create_collection(
            name=collection_name,
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
        metadatas = [exp.dict() for exp in experiences]

        AddNewExperiences._record_experiences_local(experiences)

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def add_from_file(self, file_path):
        with open(file_path, "r") as fl:
            lines = fl.readlines()
        experiences = [RoleExperience(**json.loads(line)) for line in lines]
        experiences = [exp for exp in experiences if len(exp.reflection) > 2] # not "" or not '""'

        ids = [exp.id for exp in experiences]
        documents = [exp.reflection for exp in experiences]
        metadatas = [exp.dict() for exp in experiences]

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    @staticmethod
    def _record_experiences_local(experiences: list[RoleExperience]):
        round_id = experiences[0].round_id
        version = experiences[0].version
        version = "test" if not version else version
        experiences = [exp.json() for exp in experiences]
        experience_folder = WORKSPACE_ROOT / f'werewolf_game/experiences/{version}'
        if not os.path.exists(experience_folder):
            os.makedirs(experience_folder)
        save_path = f"{experience_folder}/{round_id}.json"
        with open(save_path, "a") as fl:
            fl.write("\n".join(experiences))
            fl.write("\n")
        logger.info(f"experiences saved to {save_path}")

class RetrieveExperiences(Action):

    def __init__(
        self, name="RetrieveExperiences", context=None, llm=None, collection_name=DEFAULT_COLLECTION_NAME):
        super().__init__(name, context, llm)
        chroma_client = chromadb.PersistentClient(path=f"{WORKSPACE_ROOT}/werewolf_game/chroma")
        try:
            self.collection = chroma_client.get_collection(
                name=collection_name,
                embedding_function=EMB_FN,
            )
            self.has_experiences = True
        except:
            logger.warning(f"No experience pool {collection_name}")
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
        if not self.has_experiences or len(query) <= 2: # not "" or not '""'
            return ""
        
        filters = {"profile": profile}
        ### 消融实验逻辑 ###
        if profile == "Werewolf": # 狼人作为基线，不用经验
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
            print(*past_experiences, sep="\n\n")
            distances = results["distances"][0]
            print(distances)

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
            (template.replace("__i__", str(i)).replace("__situation__", exp.reflection)
            .replace("__instruction__", exp.instruction).replace("__response__", exp.response)
            .replace("__game_step__", exp.game_setup.replace("0 | Game setup:\n", "").replace("\n", " "))
            .replace("__outcome__", exp.outcome))
            for i, exp in enumerate(past_experiences)
        ]
        print(*past_experiences, sep="\n")
        logger.info("retrieval done")

        return json.dumps(past_experiences)

# FIXME: below are some utility functions, should be moved to appropriate places
def delete_collection(name):
    chroma_client = chromadb.PersistentClient(path=f"{WORKSPACE_ROOT}/werewolf_game/chroma")
    chroma_client.delete_collection(name=name)

def add_file_batch(folder, **kwargs):
    action = AddNewExperiences(**kwargs)
    file_paths = glob.glob(str(folder) + "/*")
    for fp in file_paths:
        print(fp)
        action.add_from_file(fp)

def modify_collection():
    chroma_client = chromadb.PersistentClient(path=f"{WORKSPACE_ROOT}/werewolf_game/chroma")
    collection = chroma_client.get_collection(name=DEFAULT_COLLECTION_NAME)
    updated_name = DEFAULT_COLLECTION_NAME + "_backup"
    collection.modify(name=updated_name)
    try:
        chroma_client.get_collection(name=DEFAULT_COLLECTION_NAME)
    except:
        logger.info(f"collection {DEFAULT_COLLECTION_NAME} not found")
    updated_collection = chroma_client.get_collection(name=updated_name)
    print(updated_collection.get()["documents"][-5:])

# if __name__ == "__main__":
    # delete_collection(name="test")
    # add_file_batch(WORKSPACE_ROOT / 'werewolf_game/experiences', collection_name=DEFAULT_COLLECTION_NAME, delete_existing=True)
    # modify_collection()
