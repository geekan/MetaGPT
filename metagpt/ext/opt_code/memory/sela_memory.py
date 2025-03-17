from metagpt.ext.opt_code.memory.tree import TreeNode, Tree
from metagpt.ext.opt_code.opt_roles.sela_role import SelaRole

import json
import numpy as np
import pandas as pd
import os
import shutil
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, roc_auc_score


def evaluate_score(pred, gt, metric):
    if metric == "accuracy":
        return accuracy_score(gt, pred)
    elif metric == "f1":
        unique_classes = sorted(list(np.unique(gt)))
        if 1 in unique_classes and 0 in unique_classes:
            pos_label = 1
        else:
            pos_label = unique_classes[0] if len(unique_classes) == 2 else None
        return f1_score(gt, pred, pos_label=pos_label)
    elif metric == "f1 weighted":
        return f1_score(gt, pred, average="weighted")
    elif metric == "roc_auc":
        return roc_auc_score(gt, pred)
    elif metric == "rmse":
        return mean_squared_error(gt, pred, squared=False)
    elif metric == "log rmse":
        return mean_squared_error(np.log1p(gt), np.log1p(pred), squared=False)
    else:
        raise ValueError(f"Metric {metric} not supported")


class SelaNode(TreeNode):
    code: list[str] = []
    role_path: str = None
    visit_count: int = 0
    normalized_reward: dict = {"train_score": 0, "dev_score": 0, "test_score": 0}
    raw_value: float = 0
    raw_reward: dict = {}
    state: dict = None
    action: str = None
    tasks: list[str] = []
    outputs: list[str] = []

    def avg_value(self):
        if self.visit_count == 0:
            return 0
        return self.reward / self.visit_count
    
    def save_new_role(self, role: SelaRole):
        new_role = role.model_copy()
        new_role.node_id = self.id
        new_role.start_task_id = self.state["start_task_id"]
        new_role.state_saved = False
        new_role.change_next_instruction(self.action)
        new_role = new_role.model_copy()
        new_role.save_state(static_save=True)

    def get_gt(self, split):
        gt_path = os.path.join(self.state["datasets_dir"][f"{split}_target"])
        return pd.read_csv(gt_path)

    def evaluate_prediction(self, split):
        preds = self.get_and_move_predictions(split)["target"]
        gt = self.get_gt(split)["target"]
        metric = self.state["dataset_config"]["metric"]
        return evaluate_score(preds, gt, metric)
    
    def avg_value(self):
        if self.visit_count == 0:
            return 0
        return self.reward / self.visit_count
    
    def get_predictions_path(self, split):
        path = os.path.join(self.state["node_dir"], f"Node_{self.id}_{split}_predictions.csv")
        print(path)
        return path

    def get_and_move_predictions(self, split):
        if not os.path.exists(self.get_predictions_path(split)):
            pred_path = os.path.join(self.state["work_dir"], f"{split}_predictions.csv")
            shutil.copy(pred_path, self.get_predictions_path(split))
            os.remove(pred_path)
        return pd.read_csv(self.get_predictions_path(split))

    def evaluate_simulation(self, score_dict: dict):
        if self.state["external_eval"]:  # use external evaluation
            scores = {"dev_score": self.evaluate_prediction("dev"), "test_score": self.evaluate_prediction("test")} #TODO
            scores["score"] = scores["dev_score"]
            score_dict.update(scores)
        else:
            self.get_and_move_predictions("dev") #TODO
            self.get_and_move_predictions("test")
        return score_dict

    def update(self, reward: dict, child_node=None, path=""):
        if child_node is not None:
            tmp_child_role = SelaRole().load_state(child_node)
            tmp_role = SelaRole().load_state(self)

            tmp_role.update_til_start_task(tmp_child_role)
            tmp_role.save_state()
        else:
            self.raw_value = reward["test_score"]
        self.reward += reward["score"]
        self.visit_count += 1
        self.save_node(path=path)

    def extend_child(self, action):
        role = SelaRole().load_state(self)
        new_state = self.state.copy()
        new_state["start_task_id"] += 1

        child = SelaNode(id=f"{self.id}_{len(self.children)}", parent=self, state=new_state, action=action, depth=self.depth + 1)
        child.save_new_role(role)
        child.tasks = role.planner.plan.tasks

        self.children.append(child)
        return child
    
    def update_from_child(self, child):
        pass

    def update_from_results(self, results):
        pass

class SelaMemory(Tree):
    c_explore: float = 1.4
    c_unvisited: float = 0.8
    node_pointer: int = 0

    def init_root_node(self, args):
        return SelaNode(id="0", state=args["state"], depth=0)
        
    # def select(self):
    #     def uct(node: SelaNode):
    #         n_visits = node.visit_count if node.visit_count else self.c_unvisited
    #         avg_value = node.avg_value() if node.visit_count else node.reward / self.c_unvisited
    #         return avg_value + self.c_explore * np.sqrt(np.log(node.parent.visit_count) / n_visits)

    #     if len(self.node_list) == 1:
    #         return self.node_list[0]
        
    #     all_children = self.node_list[1:]
    #     node = max(all_children, key=uct)

    #     self.node_pointer = self.node_list.index(node)
    #     return node

    def create_new_node(self, results):
        parent = self.node_list[self.node_pointer]

        new_state = parent.state.copy()
        new_state["start_task_id"] += 1

        child = SelaNode(parent=parent, state=new_state, action=results["new_instruction"], id=f"{parent.id}_{len(parent.children)}")
        child.save_new_role(results["role"])

    def update_from_child(self, node: SelaNode, results):
        child = node
        node.update(results, path=self.root_path)
        node = node.parent
        while node is not None:
            node.update(results, child, path=self.root_path)
            node, child = node.parent, node