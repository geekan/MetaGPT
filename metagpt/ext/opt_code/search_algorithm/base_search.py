from abc import ABC, abstractmethod
from metagpt.ext.opt_code.memory.base_memory import TreeMemory

class Search(ABC):
    def __init__(self, memory: TreeMemory, dataset: str):
        self.memory = memory
        self.dataset = dataset

    @abstractmethod
    async def search(self, optimize_agent, evaluator, max_round):
        pass
