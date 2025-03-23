from metagpt.core.utils.yaml_model import YamlModel


class OmniParseConfig(YamlModel):
    api_key: str = ""
    base_url: str = ""
    timeout: int = 600
