from pydantic import Field

from metagpt.utils.yaml_model import YamlModel


class ExperiencePoolConfig(YamlModel):
    enable_read: bool = Field(default=False, description="Enable to read from experience pool.")
    enable_write: bool = Field(default=False, description="Enable to write to experience pool.")
    persist_path: str = Field(default=".chroma_exp_data", description="The persist path for experience pool.")
