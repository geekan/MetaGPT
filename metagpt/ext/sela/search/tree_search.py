import json
import os
import pickle
import shutil

import numpy as np
import pandas as pd

from metagpt.ext.sela.data.custom_task import (
    get_mle_bench_requirements,
    get_mle_task_id,
)
from metagpt.ext.sela.data.dataset import (
    generate_task_requirement,
    get_split_dataset_path,
)
from metagpt.ext.sela.evaluation.evaluation import evaluate_score
from metagpt.ext.sela.experimenter import Experimenter, TimeoutException
from metagpt.ext.sela.insights.instruction_generator import InstructionGenerator
from metagpt.ext.sela.utils import get_exp_pool_path, load_execute_notebook, mcts_logger
from metagpt.tools.tool_recommend import ToolRecommender
from metagpt.utils.common import read_json_file


def initialize_di_root_node(state: dict, reflection: bool = True):
    """
    Initialize the root node of the decision tree.

    Args:
        state (dict): The initial state of the tree, containing:
            - task (str): The task to be performed (e.g., "titanic").
            - work_dir (str): The working directory.
            - node_dir (str): The directory for the node.
            - dataset_config (dict): The configuration of the dataset.
            - datasets_dir (str): The directory of the datasets.
            - exp_pool_path (str): The path to the experiment pool.
            - requirement (str): The requirement for the task.
            - has_run (bool): Whether the task has run.
            - start_task_id (int): The ID of the starting task.
            - low_is_better (bool): Whether a lower score is better.
            - role_timeout (int): The timeout for the role.
            - external_eval (bool): Whether to use external evaluation.
            - custom_dataset_dir (str): The directory of the custom dataset.
        reflection (bool, optional): Whether to use reflection. Defaults to True.

    Returns:
        tuple: A tuple containing the Experimenter role and the root Node.
    """
    role = Experimenter(
        node_id="0",
        start_task_id=state["start_task_id"],
        use_reflection=reflection,
        role_dir=state["node_dir"],
        role_timeout=state["role_timeout"],
    )
    return role, Node(parent=None, state=state, action=None, value=0)


def create_initial_state(task: str, start_task_id: int, data_config: dict, args):
    """
    Create the initial state of the tree.

    Args:
        task (str): The task to be performed.
        start_task_id (int): The ID of the starting task.
        data_config (dict): The configuration of the data.
            Expected keys: 'datasets', 'work_dir', 'role_dir'.
        args (Namespace): The arguments passed to the program.
            Expected attributes: 'external_eval', 'custom_dataset_dir', 'special_instruction', 'name', 'low_is_better', 'role_timeout'.

    Returns:
        dict: The initial state of the tree.
    """
    external_eval = args.external_eval

    if args.custom_dataset_dir:
        dataset_config = None
        datasets_dir = args.custom_dataset_dir
        requirement = get_mle_bench_requirements(
            args.custom_dataset_dir, data_config, special_instruction=args.special_instruction
        )
        exp_pool_path = None
        # external_eval = False # make sure external eval is false if custom dataset is used
        task = get_mle_task_id(args.custom_dataset_dir)
    else:
        dataset_config = data_config["datasets"][task]
        if dataset_config["metric"] == "rmse":
            args.low_is_better = True
        datasets_dir = get_split_dataset_path(task, data_config)
        requirement = generate_task_requirement(
            task, data_config, is_di=True, special_instruction=args.special_instruction
        )
        exp_pool_path = get_exp_pool_path(task, data_config, pool_name="ds_analysis_pool")

    initial_state = {
        "task": task,
        "work_dir": data_config["work_dir"],
        "node_dir": os.path.join(data_config["work_dir"], data_config["role_dir"], f"{task}{args.name}"),
        "dataset_config": dataset_config,
        "datasets_dir": datasets_dir,  # won't be used if external eval is used
        "exp_pool_path": exp_pool_path,
        "requirement": requirement,
        "has_run": False,
        "start_task_id": start_task_id,
        "low_is_better": args.low_is_better,
        "role_timeout": args.role_timeout,
        "external_eval": external_eval,
        "custom_dataset_dir": args.custom_dataset_dir,
    }
    os.makedirs(initial_state["node_dir"], exist_ok=True)
    return initial_state


class Node:
    state: dict = {}
    action: str = None
    value: float = 0
    visited: int = 0
    children: list = []
    normalized_reward: dict = {"train_score": 0, "dev_score": 0, "test_score": 0}
    parent = None

    def __init__(
        self, parent=None, state: dict = None, action: str = None, value: float = 0, max_depth: int = 4, **kwargs
    ):
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
        with open(os.path.join(self.state["node_dir"], f"Node-{self.id}.pkl"), "wb") as f:
            pickle.dump(self, f)

    def load_node(self):
        with open(os.path.join(self.state["node_dir"], f"Node-{self.id}.pkl"), "rb") as f:
            return pickle.load(f)

    def get_depth(self):
        return self.depth

    def get_node_dir(self):
        return self.state["node_dir"]

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
        return int(self.state["start_task_id"]) == self.max_depth + 1  # TODO: Check if this is correct or +1

    def is_fully_expanded(self):
        return len(self.children) > 0

    def add_child(self, child_node):
        self.children.append(child_node)

    def update(self, reward: dict, child_node=None):
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
        if role_dict.get("tool_recommender") is None:
            role_dict["tool_recommender"] = ToolRecommender()
        elif isinstance(role_dict.get("tool_recommender", {}).get("tools"), dict):
            role_dict["tool_recommender"]["tools"] = list(role_dict["tool_recommender"]["tools"].keys())
        role = Experimenter(**role_dict)
        if self.parent is not None:  # TODO: Check this
            parent_role = self.parent.load_role()
            role.update_til_start_task(parent_role, backward=False)
        role.remap_tasks()
        return role

    def save_new_role(self, role: Experimenter):
        role.node_id = self.id
        role.start_task_id = self.state["start_task_id"]
        role.state_saved = False
        role.change_next_instruction(self.action)
        mcts_logger.log("MCTS", f"Saving new role: {role.node_id}")
        role = role.model_copy()
        role.save_state(static_save=True)

    async def expand(self, max_children: int, instruction_generator: InstructionGenerator):
        if self.is_fully_expanded():
            return
        role = self.load_role()
        original_instruction = role.get_next_instruction()
        insights = await instruction_generator.generate_new_instructions(
            task_id=role.start_task_id + 1,
            original_instruction=original_instruction,
            max_num=max_children,
        )
        new_state = self.state.copy()
        new_state["start_task_id"] += 1
        for insight in insights:
            new_role = role.model_copy()
            node = Node(parent=self, state=new_state, action=insight, value=0)
            node.save_new_role(new_role)
            self.add_child(node)

    def get_predictions_path(self, split):
        return os.path.join(self.state["node_dir"], f"Node-{self.id}-{split}_predictions.csv")

    def get_and_move_predictions(self, split):
        if not os.path.exists(self.get_predictions_path(split)):
            pred_path = os.path.join(self.state["work_dir"], self.state["task"], f"{split}_predictions.csv")
            shutil.copy(pred_path, self.get_predictions_path(split))
            os.remove(pred_path)
        return pd.read_csv(self.get_predictions_path(split))

    def get_gt(self, split):
        gt_path = os.path.join(self.state["datasets_dir"][f"{split}_target"])
        return pd.read_csv(gt_path)

    def evaluate_prediction(self, split):
        preds = self.get_and_move_predictions(split)["target"]
        gt = self.get_gt(split)["target"]
        metric = self.state["dataset_config"]["metric"]
        return evaluate_score(preds, gt, metric)

    def evaluate_simulation(self, score_dict):
        if self.state["external_eval"]:  # use external evaluation
            scores = {"dev_score": self.evaluate_prediction("dev"), "test_score": self.evaluate_prediction("test")}
            scores["score"] = scores["dev_score"]
            score_dict.update(scores)
        else:
            self.get_and_move_predictions("dev")
            self.get_and_move_predictions("test")
        return score_dict

    async def run_node(self, role: Experimenter = None):
        if self.is_terminal() and role is not None:
            if role.state_saved:
                return self.raw_reward

        max_retries = 3
        num_runs = 1
        run_finished = False
        while num_runs <= max_retries and not run_finished:
            try:
                if not role:
                    role = self.load_role()
                    await load_execute_notebook(role)  # execute previous notebook's code
                    await role.run(with_message="continue")
                else:
                    await role.run(with_message=self.state["requirement"])
                score_dict = await role.get_score()
                score_dict = self.evaluate_simulation(score_dict)
                self.raw_reward = score_dict
                run_finished = True
            except TimeoutException as e:
                mcts_logger.log("MCTS", f"Role-level timeout: {e}")
                break
            except Exception as e:
                mcts_logger.log("MCTS", f"Error in running the role: {e}")
                num_runs += 1

        if not run_finished:
            mcts_logger.log("MCTS", f"Role {role.node_id} failed to run")
            if self.state["low_is_better"]:
                score_dict = {"test_score": np.inf, "dev_score": np.inf, "score": np.inf}
            else:
                score_dict = {"test_score": 0, "dev_score": 0, "score": 0}
            self.raw_reward = score_dict
        if self.state["low_is_better"]:
            # normalized the score to be between 0 and 1, and higher is better
            def normalize_score(score):
                if score == -1:
                    return 0
                return 1 / (1 + score)

            score_dict = {k: normalize_score(v) for k, v in score_dict.items()}
        self.normalized_reward = score_dict
        result_dict = role.get_solution()
        return score_dict, result_dict


class BaseTreeSearch:
    # data_path
    root_node: Node = None
    children: dict = {}
    max_depth: int = None
    c_explore: float = 1.4
    c_unvisited: float = 0.8
    node_order: list = []
    # insight generator
    instruction_generator: InstructionGenerator = None

    def __init__(self, root_node: Node, max_depth: int, use_fixed_insights: bool):
        self.root_node = root_node
        self.max_depth = max_depth
        self.use_fixed_insights = use_fixed_insights

    def select(self, node: Node):
        node = self.best_child()
        mcts_logger.log("MCTS", f"Selected node id: {node.id}")
        return node

    def best_child(self):
        raise NotImplementedError

    async def expand(self, node: Node, max_children=5):
        await node.expand(max_children, self.instruction_generator)
        if node not in self.children or not self.children[node]:
            self.children[node] = node.children
        return node.children

    async def simulate(self, node: Node, role=None):
        "Returns the reward for a random simulation (to completion) of `node`"
        mcts_logger.log("MCTS", f"Start simulating node {node.id}:")
        while node.children:
            node = np.random.choice(node.children)
        reward, result_dict = await node.run_node(role)
        mcts_logger.log("MCTS", f"Simulated node's reward: {reward}")
        # TODO: add new insights
        return reward

    def backpropagate(self, node: Node, reward: dict):
        child_node = node
        node.update(reward)
        node = node.parent
        while node is not None:
            node.update(reward, child_node)
            node, child_node = node.parent, node

    def best_path(self, root: Node):
        best_child = root
        global_best_score = root.normalized_reward["test_score"]
        dev_best_score = root.normalized_reward["dev_score"]

        def bfs(node: Node, best_score: float, best_child: Node, split: str):
            assert split in ["test_score", "dev_score"]
            if node not in self.children:
                return best_score, best_child
            for child in self.children[node]:
                score = child.normalized_reward[split]
                print(child.id, split, score)
                if score > best_score:
                    best_score = score
                    best_child = child
                best_score, best_child = bfs(child, best_score, best_child, split)
            return best_score, best_child

        _, global_best_child = bfs(root, global_best_score, best_child, "test_score")
        _, dev_best_child = bfs(root, dev_best_score, best_child, "dev_score")

        return {"dev_best": dev_best_child, "global_best": global_best_child, "scores": self.get_score_order_dict()}

    def get_num_simulations(self):
        return self.root_node.visited

    def save_node_order(self, node_id: str):
        self.node_order.append(node_id)
        with open(os.path.join(self.root_node.state["node_dir"], "node_order.json"), "w") as f:
            json.dump(self.node_order, f)

    def load_node_order(self):
        with open(os.path.join(self.root_node.state["node_dir"], "node_order.json"), "r") as f:
            self.node_order = json.load(f)

    def get_score_order_dict(self):
        scores = {"dev": [], "test": [], "dev_raw": [], "test_raw": []}
        for node_id in self.node_order:
            node = Node(parent=None, state=self.root_node.state, action=None, value=0)
            node.id = node_id
            node = node.load_node()
            scores["dev"].append(node.normalized_reward["dev_score"])
            scores["test"].append(node.normalized_reward["test_score"])
            scores["dev_raw"].append(node.raw_reward["dev_score"])
            scores["test_raw"].append(node.raw_reward["test_score"])
        return scores

    async def search(self, state: dict, args, data_config):
        reflection = args.reflection
        load_tree = args.load_tree
        rollouts = args.rollouts
        from_scratch = args.from_scratch
        role, root = initialize_di_root_node(state, reflection=reflection)
        self.root_node = root
        self.instruction_generator = InstructionGenerator(
            state=state, use_fixed_insights=self.use_fixed_insights, from_scratch=from_scratch, data_config=data_config
        )
        await self.instruction_generator.initialize()

        tree_loaded = False
        if load_tree:
            tree_loaded = self.load_tree()
            mcts_logger.log("MCTS", f"Number of simulations: {self.get_num_simulations()}")
            mcts_logger.log("MCTS", f"Tree loaded: {tree_loaded}")

        if not tree_loaded:
            rollouts -= 2  # 2 rollouts for the initial tree
            if rollouts < 0:
                raise ValueError("Rollouts must be greater than 2 if there is no tree to load")
            self.children[root] = []
            reward = await self.simulate(root, role)
            self.backpropagate(root, reward)
            node, reward = await self.expand_and_simulate(root)
            # self.backpropagate(node, reward)
            self.save_node_order(root.id)
            self.save_node_order(node.id)
        else:
            root = self.root_node
            self.load_node_order()

        for _ in range(rollouts):  # number of rollouts
            mcts_logger.log("MCTS", f"Start the next rollout {_+1}")
            node = self.select(root)
            if node.is_terminal():
                if node.raw_value == 0:
                    reward = await self.simulate(node)
                else:
                    reward = {"test_score": node.raw_value, "score": node.raw_reward["score"]}
                mcts_logger.log("MCTS", f"Terminal node's reward: {reward}")
                self.backpropagate(node, reward)
            else:
                node, reward = await self.expand_and_simulate(node)
                # self.backpropagate(node, reward)
            self.save_node_order(node.id)
        return self.best_path(root)

    async def expand_and_simulate(self, node: Node):
        # Expand and randomly select a child node, then simulate it
        if node.visited > 0:
            children = await self.expand(node)
            node = np.random.choice(children)
        reward = await self.simulate(node)
        self.backpropagate(node, reward)
        return node, reward

    def load_tree(self):
        def load_children_node(node: Node):
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
            with open(os.path.join(self.root_node.state["node_dir"], "Node-0.pkl"), "rb") as f:
                self.root_node = pickle.load(f)
            self.children[self.root_node] = self.root_node.children
            load_children_node(self.root_node)

            if self.children:
                return True
        return False
