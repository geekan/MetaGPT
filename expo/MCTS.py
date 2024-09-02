import random
import math
import os
import pandas as pd
from expo.research_assistant import ResearchAssistant
from expo.insights.instruction_generator import InstructionGenerator
from expo.dataset import get_split_dataset_path, generate_task_requirement
from expo.evaluation.evaluation import evaluate_score
from expo.utils import mcts_logger, load_execute_notebook, get_exp_pool_path

from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.utils.common import write_json_file, read_json_file, format_trackback_info
import numpy as np
import pickle

def initialize_di_root_node(task, data_config, low_is_better=False, reflection=True, name=""):
    start_task_id = 2
    state = create_initial_state(task, start_task_id=start_task_id, data_config=data_config, low_is_better=low_is_better, name=name)
    role = ResearchAssistant(node_id="0", start_task_id=start_task_id, use_reflection=reflection, role_dir=state["node_dir"])
    return role, Node(parent=None, state=state, action=None, value=0) 


def create_initial_state(task, start_task_id, data_config, low_is_better, name):
    initial_state = {
        "task": task,
        "work_dir": data_config["work_dir"],
        "node_dir": os.path.join(data_config["work_dir"], data_config["role_dir"], f"{task}{name}"),
        "dataset_config": data_config["datasets"][task],
        "datasets_dir": get_split_dataset_path(task, data_config),
        "exp_pool_path": get_exp_pool_path(task, data_config, pool_name="ds_analysis_pool"),
        "requirement": generate_task_requirement(task, data_config),
        "has_run": False,
        "start_task_id": start_task_id,
        "low_is_better": low_is_better,
    }
    return initial_state


class Node():
    state : dict = {}
    action : str = None
    value : float = 0
    visited : int = 0
    children : list = []
    parent = None

    def __init__(self, parent=None, state = None, action=None, value = 0, max_depth=4, **kwargs):
        self.state = state
        self.action = action
        self.value = value
        self.raw_value = 0
        self.raw_reward = dict()
        self.parent = parent
        self.children = []
        self.max_depth = max_depth
        self.depth = self.generate_depth()
        self.id = self.generate_id()
        if self.parent is not None:
            self.save_node()

    def avg_value(self):
        if self.visited == 0:
            return 0
        return self.value / self.visited

    def __hash__(self):
        return hash(self.id)
    
    def save_node(self):
        os.makedirs(self.state["node_dir"], exist_ok=True)        
        with open(os.path.join(self.state["node_dir"], f"Node-{self.id}.pkl"), 'wb') as f:
            pickle.dump(self, f)
    
    def load_node(self):
        with open(os.path.join(self.state["node_dir"], f"Node-{self.id}.pkl"), 'rb') as f:
            return pickle.load(f)

    def get_depth(self):
        return self.depth

    def generate_depth(self):
        if self.parent is None:
            return 0
        else:
            return self.parent.depth + 1

    def generate_id(self):
        if self.parent is None:
            return "0"
        else:
            num_sibling = len(self.parent.children)
            return f"{self.parent.id}-{num_sibling}"

    def is_terminal(self):
        return int(self.state["start_task_id"]) == self.max_depth + 1
    
    def is_fully_expanded(self):
        return len(self.children) > 0
    
    def add_child(self, child_node):
        self.children.append(child_node)

    def update(self, reward:dict, child_node=None):
        if child_node is not None:
            child_role = child_node.load_role()
            role = self.load_role()
            role.update_til_start_task(child_role)
            role.save_state()
        else:
            self.raw_value = reward["test_score"]
        self.value += reward["score"]
        self.visited += 1
        self.save_node()

    def get_role_path(self):
        fname = f"Node-{self.id}.json"
        role_path = os.path.join(self.state["node_dir"], fname)
        return role_path
    
    def load_role(self):
        role_dict = read_json_file(self.get_role_path())
        if role_dict.get('tool_recommender') is None:
            role_dict['tool_recommender'] = ToolRecommender() 
        elif isinstance(role_dict.get('tool_recommender', {}).get('tools'), dict):
            role_dict['tool_recommender']['tools'] = list(role_dict['tool_recommender']['tools'].keys())
        role = ResearchAssistant(**role_dict)
        if self.parent is not None: # TODO: Check this
            parent_role = self.parent.load_role()
            role.update_til_start_task(parent_role, backward=False)
        role.remap_tasks()
        return role
    
    def save_new_role(self, role: ResearchAssistant):
        role.node_id = self.id
        role.start_task_id = self.state['start_task_id']
        role.state_saved = False
        role.change_next_instruction(self.action)  
        mcts_logger.log("MCTS", f"Saving new role: {role.node_id}")
        role.save_state(static_save=True)
    
    async def expand(self, max_children):
        if self.is_fully_expanded():
            return
        insight_geneartor = InstructionGenerator()
        role = self.load_role()
        original_instruction = role.get_next_instruction()
        insights = await insight_geneartor.generate_new_instructions(task_id=role.start_task_id + 1, 
                                                                     original_instruction=original_instruction, 
                                                                     max_num=max_children,
                                                                     file_path=self.state["exp_pool_path"])
        new_state = self.state.copy()
        new_state['start_task_id'] += 1
        for insight in insights:
            new_role = role.model_copy()
            node = Node(parent=self, state=new_state, action=insight, value=0)
            node.save_new_role(new_role)
            self.add_child(node)
    
    # def evaluate_test(self):
    #     prediction_fpath = os.path.join(self.state["work_dir"], self.state["task"], "predictions.csv")
    #     predictions = pd.read_csv(prediction_fpath)["target"]
    #     # copy predictions.csv to the node_dir
    #     predictions_node_fpath = os.path.join(self.state["node_dir"], "Node-{self.id}-predictions.csv")
    #     predictions.to_csv(predictions_node_fpath, index=False)
    #     # load test_target.csv
    #     split_datasets_dir = self.state["datasets_dir"]
    #     gt = pd.read_csv(os.path.join(split_datasets_dir["test_target"]))["target"]
    #     metric = self.state["dataset_config"]["metric"]
    #     return evaluate_score(predictions, gt, metric)
    
    def evaluate_prediction(self, split):
        pred_path = os.path.join(self.state["work_dir"], self.state["task"], f"{split}_predictions.csv")
        pred_node_path = os.path.join(self.state["node_dir"], f"Node-{self.id}-{split}_predictions.csv")
        gt_path = os.path.join(self.state["datasets_dir"][f"{split}_target"])
        preds = pd.read_csv(pred_path)["target"]
        preds.to_csv(pred_node_path, index=False)
        gt = pd.read_csv(gt_path)["target"]
        metric = self.state["dataset_config"]["metric"]
        return evaluate_score(preds, gt, metric)
    
    def evaluate_simulation(self, score_dict):
        scores = {
            "dev_score": self.evaluate_prediction("dev"),
            "test_score": self.evaluate_prediction("test")
        }
        score_dict.update(scores)
        return score_dict
        
    
    async def run_node(self, role=None):
        if self.is_terminal() and role is not None:
            if role.state_saved:
                return self.raw_reward
            
        if not role:
            role = self.load_role()
            await load_execute_notebook(role) # execute previous notebook's code
            await role.run(with_message='continue')
        else:
            await role.run(with_message=self.state['requirement'])
        score_dict = await role.get_score()
        score_dict = self.evaluate_simulation(score_dict)
        self.raw_reward = score_dict
        if self.state["low_is_better"]:
            # normalized the score to be between 0 and 1, and higher is better
            def normalize_score(score):
                return 1 / (1 + score)
            score_dict = {k: normalize_score(v) for k, v in score_dict.items()}
        self.normalized_reward = score_dict
        return score_dict
    

class MCTS():
    #data_path
    root_node : Node = None
    children : dict = {}
    max_depth : int = 5
    c_explore : float = 1.4
    c_unvisited : float = 0.8

    def __init__(self, root_node, max_depth):
        self.root_node = root_node
        self.max_depth = max_depth

    def select(self, node: Node):
        node = self.best_child()
        mcts_logger.log("MCTS", f"Selected node id: {node.id}")
        return node
    
    def best_child(self):
        def uct(node: Node):
            n_visits = node.visited if node.visited else self.c_unvisited
            avg_value = node.avg_value() if node.visited else node.value/self.c_unvisited
            return avg_value + self.c_explore * math.sqrt(math.log(node.parent.visited) / n_visits)
        if len(self.children) == 0:
            return self.root_node
        all_children = [child for children in self.children.values() for child in children]
        return max(all_children, key=uct)

    async def expand(self, node : Node, max_children=4):
        await node.expand(max_children)
        if node not in self.children or not self.children[node]:
            self.children[node] = node.children
        return node.children
    
    async def simulate(self, node : Node, role=None):
        "Returns the reward for a random simulation (to completion) of `node`"
        mcts_logger.log("MCTS", f"Start simulating node {node.id}:")
        while node.children:
            node = random.choice(node.children)
        reward = await node.run_node(role)
        mcts_logger.log("MCTS", f"Simulated node's reward: {reward}")     
        return reward


    def backpropagate(self, node : Node, reward):
        child_node = node
        node.update(reward)
        node = node.parent
        while node is not None:
            node.update(reward, child_node)
            node, child_node = node.parent, node

    def best_path(self, root : Node):
        best_child = root
        best_score = 0
        def bfs(node : Node, best_score, best_child : Node, split):
            assert split in ["test_score", "dev_score"]
            if node not in self.children:
                return best_score, best_child
            for child in self.children[node]:
                score = child.normalized[split]
                print(child.id, score)
                if score > best_score:
                    best_score = score
                    best_child = child
                best_score, best_child = bfs(child, best_score, best_child)
            return best_score, best_child
        _, best_child = bfs(root, best_score, best_child, "test_score")
        _, dev_best_child = bfs(root, best_score, best_child, "dev_score")

        return {"dev_best": dev_best_child,
                "global_best": best_child}   
    
    def get_num_simulations(self):
        return self.root_node.visited

    async def search(self, task, data_config, name,
                     rollouts, load_tree=False, low_is_better=False, reflection=False):
        
        role, root = initialize_di_root_node(task, data_config, low_is_better=low_is_better, reflection=reflection, name=name)
        self.root_node = root
        tree_loaded = False
        if load_tree:
            tree_loaded = self.load_tree()
            mcts_logger.log("MCTS", f"Number of simulations: {self.get_num_simulations()}")
            mcts_logger.log("MCTS", f"Tree loaded: {tree_loaded}")

        if not tree_loaded:
            rollouts -= 2
            if rollouts < 0:
                raise ValueError("Rollouts must be greater than 2 if there is no tree to load")
            self.children[root] = []
            reward = await self.simulate(root, role)
            self.backpropagate(root, reward)
            children = await self.expand(root)
            #目前是随机选择1个，后续可以改成多个
            first_leaf = random.choice(children)
            reward = await self.simulate(first_leaf)
            self.backpropagate(first_leaf, reward)
        else:
            root = self.root_node
        # 后续迭代：使用UCT进行选择，expand并模拟和反向传播
        for _ in range(rollouts):  # number of rollouts
            mcts_logger.log("MCTS", f"Start the next rollout {_+1}")
            node = self.select(root)
            if node.is_terminal():
                if node.raw_value == 0:
                    reward = await self.simulate(node)
                else:
                    reward = {"test_score": node.raw_value, "score": node.value}
                mcts_logger.log("MCTS", f"Terminal node's reward: {reward}")
                self.backpropagate(node, reward)
            else:
                if node.visited > 0: 
                    children = await self.expand(node)
                    node = random.choice(children)
                reward = await self.simulate(node)
                self.backpropagate(node, reward)
        return self.best_path(root)


    def load_tree(self):
        def load_children_node(node):
            mcts_logger.log("MCTS", f"Load node {node.id}'s child: {node.children}")
            if node.is_terminal() or not node.children:
                return
            for child in node.children:
                child.load_node()
                self.children[child] = child.children
                load_children_node(child)
        # Load all pkl files in the node_dir
        all_pkl_files = os.listdir(self.root_node.state["node_dir"])
        all_pkl_files = [f for f in all_pkl_files if f.endswith(".pkl")]
        if os.path.exists(os.path.join(self.root_node.state["node_dir"], "Node-0.pkl")):
            with open(os.path.join(self.root_node.state["node_dir"], "Node-0.pkl"), 'rb') as f:
                self.root_node = pickle.load(f)
            self.children[self.root_node] = self.root_node.children
            load_children_node(self.root_node)
            if self.children:
                return True
        return False