from expo.MCTS import MCTS, Node, initialize_di_root_node
from expo.utils import load_data_config
from expo.dataset import generate_task_requirement
from expo.evaluation.visualize_mcts import get_tree_text
import asyncio
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, default="")
    get_di_args(parser)
    get_mcts_args(parser)
    get_aug_exp_args(parser)
    

    return parser.parse_args()


def get_mcts_args(parser):
    parser.add_argument("--load_tree", dest="load_tree", action="store_true")
    parser.add_argument("--no_load_tree", dest="load_tree", action="store_false")
    parser.set_defaults(load_tree=True)
    parser.add_argument("--rollout", type=int, default=3)

def get_aug_exp_args(parser):
    parser.add_argument("--aug_mode", type=str, default="single", choices=["single", "set"])
    parser.add_argument("--num_experiments", type=int, default=2)


def get_di_args(parser):
    parser.add_argument("--task", type=str, default="titanic")
    parser.add_argument("--low_is_better", dest="low_is_better", action="store_true")
    parser.set_defaults(low_is_better=False)
    parser.add_argument("--reflection", dest="reflection", action="store_true")
    parser.add_argument("--no_reflection", dest="reflection", action="store_false")
    parser.set_defaults(reflection=True)
    

async def main(args):
    pass

if __name__ == "__main__":
    args = get_args()
    asyncio.run(main(args))