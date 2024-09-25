from pydantic import Field

from metagpt.utils.yaml_model import YamlModel


class RoleZeroConfig(YamlModel):
    enable_longterm_memory: bool = Field(default=False, description="Whether to use long-term memory.")
