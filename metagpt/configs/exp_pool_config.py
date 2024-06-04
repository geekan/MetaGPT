from pydantic import Field

from metagpt.utils.yaml_model import YamlModel


class ExperiencePoolConfig(YamlModel):
    enable_read: bool = Field(default=True, description="Enable to read from experience pool.")
    enable_write: bool = Field(default=True, description="Enable to write to experience pool.")
