from metagpt.ext.opt_code.memory.tree import TreeNode, Tree

import numpy as np

class AFlowNode(TreeNode):
    modification_info: str = None
    prompt: str = None
    log_data: list[dict] = []
    experience: dict = {"success": {}, "failure": {}}

    def expand_child(self, action=None):
        return AFlowNode(
            id = f"{self.id}_{len(self.children)}",
            parent = self,
            depth = self.depth + 1,
            code = self.code,
            prompt = self.prompt
        )

    def update_from_results(self, results):
        self.reward = results["score"]
        self.log_data = results["log_data"]

    def update_from_child(self, child):
        self.update_exp_from_child(child)

    def update_exp_from_child(self, child: 'AFlowNode'):
        if child.reward - self.reward >= 0:
            self.experience["success"][child.id] = child.modification_info
        else:
            self.experience["failure"][child.id] = child.modification_info

    def extend_child(self, action):
        pass

class AFlowMemory(Tree):
    k_selected: int = 3

    def init_root_node(self, args):
        root_node = AFlowNode(
            code = args["init_code"],
            prompt = args["init_prompt"],
            depth = 0,
            id = "0"
        )
        return root_node
    
    # def select(self):
    #     k = self.k_selected
    #     if len(self.node_list) <= k:
    #         top_k_nodes = self.node_list
    #     else:
    #         # Select Top 3 score
    #         top_k_nodes = sorted(self.node_list, key=lambda x: x.reward, reverse=True)[:k]

    #     if self.node_list[0] not in top_k_nodes:
    #         top_k_nodes.append(self.node_list[0])

    #     def select_by_prob(items):
    #         sorted_items = sorted(items, key=lambda x: x.reward, reverse=True)
    #         scores = [item.reward for item in sorted_items]

    #         # transform score to probabilities
    #         probabilities = [np.exp(score) for score in scores]
    #         probabilities = probabilities / np.sum(probabilities)

    #         selected_index = np.random.choice(len(sorted_items), p=probabilities)

    #         return sorted_items[selected_index]
        
    #     return select_by_prob(top_k_nodes)

    def create_new_node(self, results):
        node = AFlowNode(
            code = results["graph"],
            prompt = results["prompt"],
            modification_info=results["modification"],
            reward = results["score"],
            log_data=results["log_data"]
        )
        return node
    
