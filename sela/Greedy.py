import random

from sela.MCTS import MCTS


class Greedy(MCTS):
    def best_child(self):
        if len(self.children) == 0:
            return self.root_node
        all_children = [child for children in self.children.values() for child in children]
        return max(all_children, key=lambda x: x.normalized_reward.get("dev_score", 0))


class Random(MCTS):
    def best_child(self):
        if len(self.children) == 0:
            return self.root_node
        all_children = [child for children in self.children.values() for child in children]
        return random.choice(all_children)
