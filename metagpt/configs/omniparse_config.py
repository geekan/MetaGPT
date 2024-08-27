from metagpt.utils.yaml_model import YamlModel


class OmniParseConfig(YamlModel):
    url: str = ""
    timeout: int = 600
