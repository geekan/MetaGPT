import json
from typing import Optional

import chromadb
from pydantic import model_validator

from metagpt.actions import Action
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.environment.werewolf.const import RoleType
from metagpt.ext.werewolf.schema import RoleExperience
from metagpt.logs import logger
from metagpt.rag.engines.simple import SimpleEngine
from metagpt.rag.schema import ChromaIndexConfig, ChromaRetrieverConfig
from metagpt.utils.common import read_json_file, write_json_file

DEFAULT_COLLECTION_NAME = "role_reflection"  # FIXME: some hard code for now
PERSIST_PATH = DEFAULT_WORKSPACE_ROOT.joinpath("werewolf_game/chroma")
PERSIST_PATH.mkdir(parents=True, exist_ok=True)


class AddNewExperiences(Action):
    name: str = "AddNewExperience"
    collection_name: str = DEFAULT_COLLECTION_NAME
    delete_existing: bool = False
    engine: Optional[SimpleEngine] = None

    @model_validator(mode="after")
    def validate_collection(self):
        if self.engine:
            return
        if self.delete_existing:
            try:
                # implement engine `DELETE` method later
                chromadb.PersistentClient(PERSIST_PATH.as_posix()).delete_collection(self.collection_name)
            except Exception as exp:
                logger.error(f"delete chroma collection: {self.collection_name} failed, exp: {exp}")

        self.engine = SimpleEngine.from_objs(
            retriever_configs=[
                ChromaRetrieverConfig(
                    persist_path=PERSIST_PATH, collection_name=self.collection_name, metadata={"hnsw:space": "cosine"}
                )
            ]
        )

    def run(self, experiences: list[RoleExperience]):
        if not experiences:
            return
        for i, exp in enumerate(experiences):
            exp.id = f"{exp.profile}-{exp.name}-step{i}-round_{exp.round_id}"

        AddNewExperiences._record_experiences_local(experiences)

        self.engine.add_objs(experiences)

    def add_from_file(self, file_path):
        experiences = read_json_file(file_path)
        experiences = [RoleExperience.model_validate(item) for item in experiences]
        experiences = [exp for exp in experiences if len(exp.reflection) > 2]  # not "" or not '""'

        self.engine.add_objs(experiences)

    @staticmethod
    def _record_experiences_local(experiences: list[RoleExperience]):
        round_id = experiences[0].round_id
        version = experiences[0].version
        version = "test" if not version else version
        experiences = [exp.model_dump() for exp in experiences]

        experience_path = DEFAULT_WORKSPACE_ROOT.joinpath(f"werewolf_game/experiences/{version}")
        experience_path.mkdir(parents=True, exist_ok=True)
        save_path = f"{experience_path}/{round_id}.json"
        write_json_file(save_path, experiences)
        logger.info(f"experiences saved to {save_path}")


class RetrieveExperiences(Action):
    name: str = "RetrieveExperiences"
    collection_name: str = DEFAULT_COLLECTION_NAME
    has_experiences: bool = True
    engine: Optional[SimpleEngine] = None
    topk: int = 10

    @model_validator(mode="after")
    def validate_collection(self):
        if self.engine:
            return
        try:
            self.engine = SimpleEngine.from_index(
                index_config=ChromaIndexConfig(
                    persist_path=PERSIST_PATH, collection_name=self.collection_name, metadata={"hnsw:space": "cosine"}
                ),
                retriever_configs=[
                    ChromaRetrieverConfig(
                        similarity_top_k=self.topk,
                        persist_path=PERSIST_PATH,
                        collection_name=self.collection_name,
                        metadata={"hnsw:space": "cosine"},
                    )
                ],
            )
        except Exception as exp:
            logger.warning(f"No experience pool: {self.collection_name}, exp: {exp}")

    def run(self, query: str, profile: str, excluded_version: str = "", verbose: bool = False) -> str:
        """_summary_

        Args:
            query (str): 用当前的reflection作为query去检索过去相似的reflection
            profile (str): _description_

        Returns:
            _type_: _description_
        """
        if not self.engine or len(query) <= 2:  # not "" or not '""'
            logger.warning("engine is None or query too short")
            return ""

        # ablation experiment logic
        if profile == RoleType.WEREWOLF.value:  # role werewolf as baseline, don't use experiences
            logger.warning("Disable werewolves' experiences")
            return ""

        results = self.engine.retrieve(query)

        logger.info(f"retrieve {profile}'s experiences")
        experiences = [res.metadata["obj"] for res in results]

        past_experiences = []  # currently use post-process to filter, and later add `filters` in rag
        for exp in experiences:
            if exp.profile == profile and exp.version != excluded_version:
                past_experiences.append(exp)

        if verbose and results:
            logger.info("past_experiences: {}".format("\n\n".join(past_experiences)))
            distances = results[0].score
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
