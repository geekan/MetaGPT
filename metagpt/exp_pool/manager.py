"""Experience Manager."""

from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel, ConfigDict, model_validator

from metagpt.config2 import Config, config
from metagpt.exp_pool.schema import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_SIMILARITY_TOP_K,
    EntryType,
    Experience,
    Metric,
    QueryType,
    Score,
)
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import ChromaRetrieverConfig, LLMRankerConfig
from metagpt.strategy.experience_retriever import ENGINEER_EXAMPLE, TL_EXAMPLE
from metagpt.utils.exceptions import handle_exception


class ExperienceManager(BaseModel):
    """ExperienceManager manages the lifecycle of experiences, including CRUD and optimization.

    Args:
        config (Config): Configuration for managing experiences.
        storage (SimpleEngine): Engine to handle the storage and retrieval of experiences.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config = config
    storage: SimpleEngine = None

    @model_validator(mode="after")
    def initialize(self):
        if self.storage is None:
            retriever_configs = [
                ChromaRetrieverConfig(
                    persist_path=self.config.exp_pool.persist_path,
                    collection_name=DEFAULT_COLLECTION_NAME,
                    similarity_top_k=DEFAULT_SIMILARITY_TOP_K,
                )
            ]
            ranker_configs = [LLMRankerConfig()]

            self.storage = SimpleEngine.from_objs(retriever_configs=retriever_configs, ranker_configs=ranker_configs)

        logger.debug(f"exp_pool config: {self.config.exp_pool}")
        return self

    @handle_exception
    def init_exp_pool(self):
        if not self.config.exp_pool.enable_write:
            return

        if self._has_exps():
            return

        self._init_teamleader_exps()
        self._init_engineer2_exps()
        logger.info("`init_exp_pool` done.")

    @handle_exception
    def create_exp(self, exp: Experience):
        """Adds an experience to the storage if writing is enabled.

        Args:
            exp (Experience): The experience to add.
        """
        if not self.config.exp_pool.enable_write:
            return

        self.storage.add_objs([exp])

    @handle_exception(default_return=[])
    async def query_exps(self, req: str, tag: str = "", query_type: QueryType = QueryType.SEMANTIC) -> list[Experience]:
        """Retrieves and filters experiences.

        Args:
            req (str): The query string to retrieve experiences.
            tag (str): Optional tag to filter the experiences by.
            query_type (QueryType): Default semantic to vector matching. exact to same matching.

        Returns:
            list[Experience]: A list of experiences that match the args.
        """
        if not self.config.exp_pool.enable_read:
            return []

        nodes = await self.storage.aretrieve(req)
        exps: list[Experience] = [node.metadata["obj"] for node in nodes]

        # TODO: filter by metadata
        if tag:
            exps = [exp for exp in exps if exp.tag == tag]

        if query_type == QueryType.EXACT:
            exps = [exp for exp in exps if exp.req == req]

        return exps

    def _has_exps(self) -> bool:
        vector_store: ChromaVectorStore = self.storage._retriever._vector_store

        return bool(vector_store._get(limit=1, where={}).ids)

    def _init_exp(self, req: str, resp: str, tag: str, metric: Metric = None):
        exp = Experience(
            req=req,
            resp=resp,
            entry_type=EntryType.MANUAL,
            tag=tag,
            metric=metric or Metric(score=Score(val=9, reason="Manual")),
        )
        self.create_exp(exp)

    def _init_teamleader_exps(self):
        self._init_exp(req=TL_EXAMPLE, resp=TL_EXAMPLE, tag="TeamLeader.llm_cached_aask")

    def _init_engineer2_exps(self):
        self._init_exp(req=ENGINEER_EXAMPLE, resp=ENGINEER_EXAMPLE, tag="Engineer2.llm_cached_aask")


exp_manager = ExperienceManager()
