import numpy as np

from metagpt.ext.sela.search.tree_search import BaseTreeSearch, Node


class Greedy(BaseTreeSearch):
    def best_child(self):
        if len(self.children) == 0:
            return self.root_node
        all_children = [child for children in self.children.values() for child in children]
        return max(all_children, key=lambda x: x.normalized_reward.get("dev_score", 0))


class Random(BaseTreeSearch):
    def best_child(self):
        if len(self.children) == 0:
            return self.root_node
        all_children = [child for children in self.children.values() for child in children]
        return np.random.choice(all_children)


class MCTS(BaseTreeSearch):
    def best_child(self):
        def uct(node: Node):
            n_visits = node.visited if node.visited else self.c_unvisited
            avg_value = node.avg_value() if node.visited else node.value / self.c_unvisited
            return avg_value + self.c_explore * np.sqrt(np.log(node.parent.visited) / n_visits)

        if len(self.children) == 0:
            return self.root_node
        all_children = [child for children in self.children.values() for child in children]
        return max(all_children, key=uct)
