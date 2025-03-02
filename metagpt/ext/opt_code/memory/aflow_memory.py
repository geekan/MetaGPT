from metagpt.ext.opt_code.memory.base_memory import CodeNode, TreeMemory
from metagpt.ext.opt_code.utils.aflow import WORKFLOW_TEMPLATE
from metagpt.logs import logger
from typing import Optional, List
import numpy as np
import json
import os

class AFlowCodeNode(CodeNode):
    def __init__(self,
                 code: str,
                 id: int,
                 file_path: str,
                 dataset: str,
                 score: Optional[float] = 0,
                 meta: Optional[dict] = {},
                 parent: Optional['CodeNode'] = None,
                 modification_info: str = None):
        super().__init__(code, id, file_path, dataset, score, meta, parent, modification_info)
        self.meta["experience"] = {"success": {}, "failure": {}}

    def write_file(self):
        os.makedirs(self.file_path, exist_ok=True)

        graph = WORKFLOW_TEMPLATE.format(graph=self.code, round=self.id, dataset=self.dataset)

        with open(os.path.join(self.file_path, "graph.py"), "w", encoding="utf-8") as file:
            file.write(graph)

        with open(os.path.join(self.file_path, "prompt.py"), "w", encoding="utf-8") as file:
            file.write(self.meta["prompt"])

        with open(os.path.join(self.file_path, "__init__.py"), "w", encoding="utf-8") as file:
            file.write("")        

    def get_executor(self, llm_config):
        workflow_path = self.file_path.replace("\\", ".").replace("/", ".")
        graph_module_name = f"{workflow_path}.graph"

        try:
            graph_module = __import__(graph_module_name, fromlist=[""])
            graph_class = getattr(graph_module, "Workflow")
            graph = graph_class(name=f"{self.dataset}_{self.id}", llm_config=llm_config, dataset=self.dataset)
            return graph
        except ImportError as e:
            logger.info(f"Error loading graph for node {self.id}: {e}")
            raise
        
class AFlowMemory(TreeMemory):
    def __init__(self, init_code, init_prompt, dataset, operators: List[str], node_class=AFlowCodeNode):
        init_meta = {"prompt": init_prompt}
        root_path = f"metagpt/ext/opt_code/optimized/aflow/{dataset}"
        self.id_counter = 0
        super().__init__(init_code, init_meta, dataset, root_path, node_class=node_class)
        self.operator_description = self._get_operator_description(operators)


    def _get_operator_description(self, operators: List[str]):
        path = f"{self.root_path}/template/operator.json"
        operators_description = ""
        for id, operator in enumerate(operators):
            operator_description = self._load_operator_description(id + 1, operator, path)
            operators_description += f"{operator_description}\n"
        return operators_description
    
    def _load_operator_description(self, id: int, operator_name: str, file_path: str) -> str:
        with open(file_path, "r") as f:
            operator_data = json.load(f)
            matched_data = operator_data[operator_name]
            desc = matched_data["description"]
            interface = matched_data["interface"]
            return f"{id}. {operator_name}: {desc}, with interface {interface})."

    def _get_id(self, parent_node=None):
        ret = self.id_counter
        self.id_counter += 1
        return ret
    
    def _get_file_path(self, id):
        return os.path.join(self.root_path, f"round_{id}")
    
    def select_node(self, k=3):
        if len(self.node_list) <= k:
            top_k_nodes = self.node_list
        else:
            # Select Top 3 score
            top_k_nodes = sorted(self.node_list, key=lambda x: x.score, reverse=True)[:k]

        if self.node_list[0] not in top_k_nodes:
            top_k_nodes.append(self.node_list[0])

        def select_by_prob(items):
            sorted_items = sorted(items, key=lambda x: x.score, reverse=True)
            scores = [item.score for item in sorted_items]

            # transform score to probabilities
            probabilities = [np.exp(score) for score in scores]
            probabilities = probabilities / np.sum(probabilities)
            
            logger.info(f"\nMixed probability distribution: {probabilities}")
            logger.info(f"\nSorted rounds: {sorted_items}")

            selected_index = np.random.choice(len(sorted_items), p=probabilities)
            logger.info(f"\nSelected index: {selected_index}, Selected item: {sorted_items[selected_index]}")

            return sorted_items[selected_index]
        
        return select_by_prob(top_k_nodes)

    def create_node(self, response, parent_node):
        code = response["graph"]
        prompt = response["prompt"]
        modification_info = response["modification"]
        id = self._get_id(parent_node)
        file_path = self._get_file_path(id)
        new_node = AFlowCodeNode(code=code, id=id, file_path=file_path, dataset=self.dataset, meta={"prompt": prompt}, parent=parent_node, modification_info=modification_info)
        self.node_list.append(new_node)
        return new_node
    
    def update_from_child(self, child):
        child_score = child.score
        parent_score = child.parent.score
        if child_score >= parent_score:
            child.parent.meta["experience"]["success"][child.id] = child.modification_info
        else:
            child.parent.meta["experience"]["failure"][child.id] = child.modification_info

    def save_report(self):
        file_path = os.path.join(self.root_path, "report.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            for node in self.node_list:
                f.write(f"Round {node.id}:\n")
                f.write(f"Score: {node.score}\n")
                f.write(f"Modification info: {node.modification_info}\n")
                f.write(f"Code: {node.code}\n")
                f.write(f"Prompt: {node.meta['prompt']}\n")
                f.write(f"Success Experience: {node.meta['experience']['success']}\nFailed Experience: {node.meta['experience']['failure']}\n")
                f.write("\n")
