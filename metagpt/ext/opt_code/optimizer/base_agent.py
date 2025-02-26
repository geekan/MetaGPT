from abc import ABC, abstractmethod
from metagpt.provider.llm_provider_registry import create_llm_instance

class Agent(ABC):
    def __init__(self, llm_config):
        self.optimizer = create_llm_instance(llm_config)

    @abstractmethod
    async def _generate_code(self, reference_code: str, context):
        pass