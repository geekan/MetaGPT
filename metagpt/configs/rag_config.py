from metagpt.utils.yaml_model import YamlModel
from metagpt.configs.embedding_config import EmbeddingConfig
from metagpt.configs.query_analysis_config import QueryAnalysisConfig


class RAGConfig(YamlModel):
    embedding: EmbeddingConfig = EmbeddingConfig()
    query_analysis: QueryAnalysisConfig = QueryAnalysisConfig()
