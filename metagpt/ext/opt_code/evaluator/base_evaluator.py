from metagpt.ext.opt_code.memory.base_memory import CodeNode
from abc import ABC, abstractmethod
import os
import time
import json

class Evaluator(ABC):
    def __init__(self, train_data_path: str, test_data_path: str, llm_config):
        self.train_data_path = train_data_path
        self.test_data_path = test_data_path
        self.llm_config = llm_config

    @abstractmethod
    def load_data(self, path):
        pass
        
    async def evaluate(self, node: CodeNode, k=3, is_test=False):
        data = []
        if is_test:
            data = self.load_data(self.test_data_path)
        else:
            data = self.load_data(self.train_data_path)

        sum_score = 0
        results = []
        executor = node.get_executor(self.llm_config)

        for _ in range(k):
            score, result = await self._evaluate(executor, data)
            sum_score += score
            results.append(result)

            # save results to jsonl
            avg_score = sum([r["Score"] for r in result]) / len(result)
            current_time = time.strftime("%Y%m%d_%H%M%S")
            if is_test:
                with open(os.path.join(node.file_path, f"test_{current_time}.json"), "w") as f:
                    content = {"avg_score": avg_score, "result": result}
                    json.dump(content, f, indent=4)
            else:
                with open(os.path.join(node.file_path, f"valid_{current_time}.json"), "w") as f:
                    content = {"avg_score": avg_score, "result": result}
                    json.dump(content, f, indent=4)

        avg_score = sum_score / k

        return avg_score, results

    @abstractmethod
    async def _evaluate(self, executor, data):
        pass
