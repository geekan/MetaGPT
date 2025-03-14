from metagpt.ext.opt_code.search_algorithm.tree_search import TreeSearch
from metagpt.ext.opt_code.memory.aflow_memory import AFlowMemory, AFlowNode
from metagpt.provider.llm_provider_registry import create_llm_instance

import json
import numpy as np

class AFlowSearch(TreeSearch):
    def __init__(self, configs):
        super().__init__(configs)
        self.configs = configs

    async def _initialize(self, node, global_context):

        path = f"{self.configs['root_path']}/template/operator.json"
        operators_description = ""
        for id, operator in enumerate(self.configs["operators"]):
            operator_description = self._load_operator_description(id + 1, operator, path)
            operators_description += f"{operator_description}\n"
        
        global_context["operators_description"] = operators_description
    
    def _load_operator_description(self, id: int, operator_name: str, file_path: str) -> str:
        with open(file_path, "r") as f:
            operator_data = json.load(f)
            matched_data = operator_data[operator_name]
            desc = matched_data["description"]
            interface = matched_data["interface"]
            return f"{id}. {operator_name}: {desc}, with interface {interface})."

    def _prepare(self, node: AFlowNode):
        exp_str = "Failure experience: " + "\n".join(node.experience["failure"]) + "\nSuccess experience: " + "\n".join(node.experience["success"])
        data_type = self.configs["data_type"]

        log_data = np.random.choice(node.log_data, 3) if len(node.log_data) > 3 else node.log_data
        log_str = "\n".join(f"Question: {log_data['question']}, Wrong Answer: {log_data['wrong_answer']}, Correct Answer: {log_data['correct_answer']}" for log_data in log_data)

        operator_description = self.global_context["operators_description"]

        return {
            "experience": exp_str,
            "operator_description": operator_description,
            "data_type": data_type,
            "log_data": log_str
        }
    
    async def _expand(self, node: AFlowNode, memory: AFlowMemory):
        child_node = node.expand_child()
        node.children.append(child_node)
        memory.node_list.append(child_node)
        return child_node
    
    def _update_global_context(self, node, results):
        pass