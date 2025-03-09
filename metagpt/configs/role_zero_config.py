from pydantic import Field

from metagpt.utils.yaml_model import YamlModel


class RoleZeroConfig(YamlModel):
    enable_longterm_memory: bool = Field(default=False, description="Whether to use long-term memory.")
    longterm_memory_persist_path: str = Field(default=".role_memory_data", description="The directory to save data.")
    memory_k: int = Field(default=200, description="The capacity of short-term memory.")
    similarity_top_k: int = Field(default=5, description="The number of long-term memories to retrieve.")
    use_llm_ranker: bool = Field(default=False, description="Whether to use LLM Reranker to get better result.")
