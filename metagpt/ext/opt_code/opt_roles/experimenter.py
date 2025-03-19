from metagpt.roles.role import Role
from metagpt.provider.llm_provider_registry import create_llm_instance
from abc import ABC, abstractmethod

class Experimenter(Role, ABC):
    async def initialize(self, node, kwargs: dict, root_path):
        self.root_path = root_path
        self.args = kwargs
        self.llm_config = kwargs["llm_config"]
        self.llm = create_llm_instance(kwargs["llm_config"])
        return await self.run(node)

    @abstractmethod
    async def run(self, node, context=None, instruction=None):
        pass

    