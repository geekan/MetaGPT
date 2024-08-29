"""Experience Manager."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from metagpt.config2 import Config
from metagpt.configs.exp_pool_config import ExperiencePoolRetrievalType
from metagpt.exp_pool.schema import DEFAULT_SIMILARITY_TOP_K, Experience, QueryType
from metagpt.logs import logger
from metagpt.utils.exceptions import handle_exception

if TYPE_CHECKING:
    from metagpt.rag.engines import SimpleEngine


class ExperienceManager(BaseModel):
    """ExperienceManager manages the lifecycle of experiences, including CRUD and optimization.

    Args:
        config (Config): Configuration for managing experiences.
        _storage (SimpleEngine): Engine to handle the storage and retrieval of experiences.
        _vector_store (ChromaVectorStore): The actual place where vectors are stored.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config = Field(default_factory=Config.default)

    _storage: Any = None

    @property
    def storage(self) -> "SimpleEngine":
        if self._storage is None:
            logger.info(f"exp_pool config: {self.config.exp_pool}")

            self._storage = self._resolve_storage()

        return self._storage

    @storage.setter
    def storage(self, value):
        self._storage = value

    @property
    def is_readable(self) -> bool:
        return self.config.exp_pool.enabled and self.config.exp_pool.enable_read

    @is_readable.setter
    def is_readable(self, value: bool):
        self.config.exp_pool.enable_read = value

        # If set to True, ensure that enabled is also True.
        if value:
            self.config.exp_pool.enabled = True

    @property
    def is_writable(self) -> bool:
        return self.config.exp_pool.enabled and self.config.exp_pool.enable_write

    @is_writable.setter
    def is_writable(self, value: bool):
        self.config.exp_pool.enable_write = value

        # If set to True, ensure that enabled is also True.
        if value:
            self.config.exp_pool.enabled = True

    @handle_exception
    def create_exp(self, exp: Experience):
        """Adds an experience to the storage if writing is enabled.

        Args:
            exp (Experience): The experience to add.
        """

        self.create_exps([exp])

    @handle_exception
    def create_exps(self, exps: list[Experience]):
        """Adds multiple experiences to the storage if writing is enabled.

        Args:
            exps (list[Experience]): A list of experiences to add.
        """
        if not self.is_writable:
            return

        self.storage.add_objs(exps)
        self.storage.persist(self.config.exp_pool.persist_path)

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

        if not self.is_readable:
            return []

        nodes = await self.storage.aretrieve(req)
        exps: list[Experience] = [node.metadata["obj"] for node in nodes]

        # TODO: filter by metadata
        if tag:
            exps = [exp for exp in exps if exp.tag == tag]

        if query_type == QueryType.EXACT:
            exps = [exp for exp in exps if exp.req == req]

        return exps

    @handle_exception
    def delete_all_exps(self):
        """Delete the all experiences."""

        if not self.is_writable:
            return

        self.storage.clear(persist_dir=self.config.exp_pool.persist_path)

    def get_exps_count(self) -> int:
        """Get the total number of experiences."""

        return self.storage.count()

    def _resolve_storage(self) -> "SimpleEngine":
        """Selects the appropriate storage creation method based on the configured retrieval type."""

        storage_creators = {
            ExperiencePoolRetrievalType.BM25: self._create_bm25_storage,
            ExperiencePoolRetrievalType.CHROMA: self._create_chroma_storage,
        }

        return storage_creators[self.config.exp_pool.retrieval_type]()

    def _create_bm25_storage(self) -> "SimpleEngine":
        """Creates or loads BM25 storage.

        This function attempts to create a new BM25 storage if the specified
        document store path does not exist. If the path exists, it loads the
        existing BM25 storage.

        Returns:
            SimpleEngine: An instance of SimpleEngine configured with BM25 storage.

        Raises:
            ImportError: If required modules are not installed.
        """

        try:
            from metagpt.rag.engines import SimpleEngine
            from metagpt.rag.schema import BM25IndexConfig, BM25RetrieverConfig
        except ImportError:
            raise ImportError("To use the experience pool, you need to install the rag module.")

        persist_path = Path(self.config.exp_pool.persist_path)
        docstore_path = persist_path / "docstore.json"

        ranker_configs = self._get_ranker_configs()

        if not docstore_path.exists():
            logger.debug(f"Path `{docstore_path}` not exists, try to create a new bm25 storage.")
            exps = [Experience(req="req", resp="resp")]

            retriever_configs = [BM25RetrieverConfig(create_index=True, similarity_top_k=DEFAULT_SIMILARITY_TOP_K)]

            storage = SimpleEngine.from_objs(
                objs=exps, retriever_configs=retriever_configs, ranker_configs=ranker_configs
            )
            return storage

        logger.debug(f"Path `{docstore_path}` exists, try to load bm25 storage.")
        retriever_configs = [BM25RetrieverConfig(similarity_top_k=DEFAULT_SIMILARITY_TOP_K)]
        storage = SimpleEngine.from_index(
            BM25IndexConfig(persist_path=persist_path),
            retriever_configs=retriever_configs,
            ranker_configs=ranker_configs,
        )

        return storage

    def _create_chroma_storage(self) -> "SimpleEngine":
        """Creates Chroma storage.

        Returns:
            SimpleEngine: An instance of SimpleEngine configured with Chroma storage.

        Raises:
            ImportError: If required modules are not installed.
        """

        try:
            from metagpt.rag.engines import SimpleEngine
            from metagpt.rag.schema import ChromaRetrieverConfig
        except ImportError:
            raise ImportError("To use the experience pool, you need to install the rag module.")

        retriever_configs = [
            ChromaRetrieverConfig(
                persist_path=self.config.exp_pool.persist_path,
                collection_name=self.config.exp_pool.collection_name,
                similarity_top_k=DEFAULT_SIMILARITY_TOP_K,
            )
        ]
        ranker_configs = self._get_ranker_configs()

        storage = SimpleEngine.from_objs(retriever_configs=retriever_configs, ranker_configs=ranker_configs)

        return storage

    def _get_ranker_configs(self):
        """Returns ranker configurations based on the configuration.

        If `use_llm_ranker` is True, returns a list with one `LLMRankerConfig`
        instance. Otherwise, returns an empty list.

        Returns:
            list: A list of `LLMRankerConfig` instances or an empty list.
        """

        from metagpt.rag.schema import LLMRankerConfig

        return [LLMRankerConfig(top_n=DEFAULT_SIMILARITY_TOP_K)] if self.config.exp_pool.use_llm_ranker else []


_exp_manager = None


def get_exp_manager() -> ExperienceManager:
    global _exp_manager
    if _exp_manager is None:
        _exp_manager = ExperienceManager()
    return _exp_manager
