from metagpt.utils.yaml_model import YamlModel


class ExperiencePoolConfig(YamlModel):
    enable_read: bool = False
    enable_write: bool = False
