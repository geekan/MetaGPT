from pydantic import Field

from metagpt.utils.yaml_model import YamlModel


class ExperiencePoolConfig(YamlModel):
    enabled: bool = Field(
        default=False,
        description="Flag to enable or disable the experience pool. When disabled, both reading and writing are ineffective.",
    )
    enable_read: bool = Field(default=False, description="Enable to read from experience pool.")
    enable_write: bool = Field(default=False, description="Enable to write to experience pool.")
    persist_path: str = Field(default=".chroma_exp_data", description="The persist path for experience pool.")
