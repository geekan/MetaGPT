"""Experience Manager."""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from metagpt.config2 import Config, config
from metagpt.exp_pool.schema import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_SIMILARITY_TOP_K,
    Experience,
    QueryType,
)
from metagpt.logs import logger
from metagpt.utils.exceptions import handle_exception

if TYPE_CHECKING:
    from llama_index.vector_stores.chroma import ChromaVectorStore


class ExperienceManager(BaseModel):
    """ExperienceManager manages the lifecycle of experiences, including CRUD and optimization.

    Args:
        config (Config): Configuration for managing experiences.
        _storage (SimpleEngine): Engine to handle the storage and retrieval of experiences.
        _vector_store (ChromaVectorStore): The actual place where vectors are stored.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config = config

    _storage: Any = None
    _vector_store: Any = None

    @property
    def storage(self):
        if self._storage is None:
            try:
                from metagpt.rag.engines import SimpleEngine
                from metagpt.rag.schema import ChromaRetrieverConfig, LLMRankerConfig
            except ImportError:
                raise ImportError("To use the experience pool, you need to install the rag module.")

            retriever_configs = [
                ChromaRetrieverConfig(
                    persist_path=self.config.exp_pool.persist_path,
                    collection_name=DEFAULT_COLLECTION_NAME,
                    similarity_top_k=DEFAULT_SIMILARITY_TOP_K,
                )
            ]
            ranker_configs = [LLMRankerConfig(top_n=DEFAULT_SIMILARITY_TOP_K)]

            self._storage: SimpleEngine = SimpleEngine.from_objs(
                retriever_configs=retriever_configs, ranker_configs=ranker_configs
            )
            logger.info(f"exp_pool config: {self.config.exp_pool}")

        return self._storage

    @property
    def vector_store(self):
        if not self._vector_store:
            self._vector_store: ChromaVectorStore = self.storage._retriever._vector_store

        return self._vector_store

    @handle_exception
    def create_exp(self, exp: Experience):
        """Adds an experience to the storage if writing is enabled.

        Args:
            exp (Experience): The experience to add.
        """

        if not self.config.exp_pool.enabled or not self.config.exp_pool.enable_write:
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

        if not self.config.exp_pool.enabled or not self.config.exp_pool.enable_read:
            return []

        nodes = await self.storage.aretrieve(req)
        exps: list[Experience] = [node.metadata["obj"] for node in nodes]

        # TODO: filter by metadata
        if tag:
            exps = [exp for exp in exps if exp.tag == tag]

        if query_type == QueryType.EXACT:
            exps = [exp for exp in exps if exp.req == req]

        return exps

    def get_exps_count(self) -> int:
        """Get the total number of experiences."""

        return self.vector_store._collection.count()


exp_manager = ExperienceManager()
