"""Experience Manager."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator

from metagpt.config2 import Config, config
from metagpt.exp_pool.schema import MAX_SCORE, Experience
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import ChromaRetrieverConfig, LLMRankerConfig


class ExperienceManager(BaseModel):
    """ExperienceManager manages the lifecycle of experiences, including CRUD and optimization.

    Attributes:
        config (Config): Configuration for managing experiences.
        storage (SimpleEngine): Engine to handle the storage and retrieval of experiences.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config = config
    storage: SimpleEngine = None

    @model_validator(mode="after")
    def initialize(self):
        if self.storage is None:
            self.storage = SimpleEngine.from_objs(
                retriever_configs=[
                    ChromaRetrieverConfig(collection_name="experience_pool", persist_path=".chroma_exp_data")
                ],
                ranker_configs=[LLMRankerConfig()],
            )
        return self

    def create_exp(self, exp: Experience):
        """Adds an experience to the storage if writing is enabled.

        Args:
            exp (Experience): The experience to add.
        """
        if not self.config.exp_pool.enable_write:
            return

        self.storage.add_objs([exp])

    async def query_exps(self, req: str, tag: str = "") -> list[Experience]:
        """Retrieves and filters experiences.

        Args:
            req (str): The query string to retrieve experiences.
            tag (str): Optional tag to filter the experiences by.

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

        return exps

    def extract_one_perfect_exp(self, exps: list[Experience]) -> Optional[Experience]:
        """Extracts the first 'perfect' experience from a list of experiences.

        Args:
            exps (list[Experience]): The experiences to evaluate.

        Returns:
            Optional[Experience]: The first perfect experience if found, otherwise None.
        """
        for exp in exps:
            if self.is_perfect_exp(exp):
                return exp

        return None

    @staticmethod
    def is_perfect_exp(exp: Experience) -> bool:
        """Determines if an experience is considered 'perfect'.

        Args:
            exp (Experience): The experience to evaluate.

        Returns:
            bool: True if the experience is manually entered, otherwise False.
        """
        if not exp:
            return False

        # TODO: need more metrics
        if exp.metric and exp.metric.score == MAX_SCORE:
            return True

        return False


exp_manager = ExperienceManager()
