from pydantic import BaseModel, ConfigDict
from metagpt.exp_pool.schema import Experience
import uuid
import chromadb
from chromadb import Collection, QueryResult
from typing import Optional
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import ChromaRetrieverConfig


class ExperiencePoolManager(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._storage = None

    @property
    def storage(self) -> SimpleEngine:
        if self._storage is None:
            self._storage = SimpleEngine.from_objs(retriever_configs=[ChromaRetrieverConfig(collection_name="experience_pool", persist_path="./chroma_data")])
        return self._storage
    
    def create_exp(self, exp: Experience):
        self.storage.add_objs([exp])
    
    async def query_exp(self, req: str) -> list[Experience]:
        nodes = await self.storage.aretrieve(req)
        exps = [node.metadata["obj"] for node in nodes]

        return exps

    

