from metagpt.configs.hyde_config import HyDEConfig
from metagpt.utils.yaml_model import YamlModel


class QueryAnalysisConfig(YamlModel):
    hyde: HyDEConfig = HyDEConfig()
