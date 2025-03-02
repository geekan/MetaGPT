from metagpt.ext.opt_code.search_algorithm.base_search import Search
from metagpt.ext.opt_code.memory.aflow_memory import AFlowMemory, AFlowCodeNode
from metagpt.ext.opt_code.evaluator.base_evaluator import Evaluator
from metagpt.ext.opt_code.optimizer.aflow_agent import AFlowAgent
import time
import traceback

class AFlowSearch(Search):
    def __init__(self, memory: AFlowMemory, dataset: str):
        super().__init__(memory, dataset)

    def _extract_failure_result(self, results: list):
        failure_result = []
        for item in results:
            for r in item:
                if r["Score"] < 0.3:
                    failure_result.append(r)

        return failure_result

    async def search(self, optimize_agent: AFlowAgent, evaluator: Evaluator, max_round=20):
        for r in range(max_round):

            retry_count = 0
            max_retries = 1

            while retry_count < max_retries:
                try:
                    if r == 0:
                        # 0. Initialize
                        node = self.memory.node_list[0]
                        avg_score, results = await evaluator.evaluate(node, is_test=False)
                        log_data = self._extract_failure_result(results)
                        node.score = avg_score
                        node.meta["log_data"] = log_data
                        # self.memory.update_from_child(node)
                        break
                    else:
                        # 1. Select
                        parent_node = self.memory.select_node()

                        # 2. Expand
                        context = {
                            "experience": parent_node.meta.get("experience", {"failure": {}, "success": {}}),
                            "score": parent_node.score,
                            "prompt": parent_node.meta["prompt"],
                            "operator_description": self.memory.operator_description,
                            "type": self.dataset,
                            "log_data": parent_node.meta.get("log_data", [])
                        }
                        response = await optimize_agent._generate_code(parent_node.code, context)

                        node = self.memory.create_node(response, parent_node)

                        # 3. Evaluate
                        avg_score, log_data = await evaluator.evaluate(node, is_test=False)
                        node.score = avg_score
                        node.meta["log_data"] = log_data

                        # 4. Backpropagation
                        self.memory.update_from_child(node)
                        break
                    
                except Exception as e:
                    retry_count += 1
                    print(f"Error generating prediction: {e}. Retrying... ({retry_count}/{max_retries})")
                    if retry_count == max_retries:
                        print("Maximum retries reached. Skipping this sample.")
                        break
                    traceback.print_exc()
                    time.sleep(5)

        # select the node of highest score
        best_node = self.memory.get_best_nodes(k=1)[0]
        print(f"Best node: {best_node.code}")

        best_score = await evaluator.evaluate(node, is_test=True)
        print(f"Best score: {best_score}")

        self.memory.save_report()
        
