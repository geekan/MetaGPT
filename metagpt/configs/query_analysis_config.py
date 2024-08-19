from metagpt.utils.yaml_model import YamlModel
from metagpt.configs.hyde_config import HyDEConfig


class QueryAnalysisConfig(YamlModel):
    hyde: HyDEConfig = HyDEConfig()
