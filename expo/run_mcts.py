from expo.MCTS import MCTS, Node, initialize_di_root_node
from expo.utils import load_data_config
from expo.dataset import generate_task_requirement

from expo.evaluation.visualize_mcts import get_tree_text
import asyncio
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="titanic")
    parser.add_argument("--low_is_better", dest="low_is_better", action="store_true")
    parser.set_defaults(low_is_better=False)
    parser.add_argument("--load_tree", dest="load_tree", action="store_true")
    parser.add_argument("--no_load_tree", dest="load_tree", action="store_false")
    parser.set_defaults(load_tree=True)
    parser.add_argument("--reflection", dest="reflection", action="store_true")
    parser.add_argument("--no_reflection", dest="reflection", action="store_false")
    parser.set_defaults(reflection=True)
    parser.add_argument("--rollout", type=int, default=3)
    parser.add_argument("--name", type=str, default="")
    return parser.parse_args()


data_config = load_data_config()

if __name__ == "__main__":
    args = get_args()
    requirement = generate_task_requirement(args.task, data_config)
    print(requirement)

    # role, root_node = initialize_di_root_node(requirement, data_config)
    # asyncio.run(role.run(requirement))

    # asyncio.run(root_node.run_node())
    mcts = MCTS(root_node=None, max_depth=5)
    best_node = asyncio.run(mcts.search(args.task, data_config, 
                                        low_is_better=args.low_is_better, load_tree=args.load_tree,
                                        reflection=args.reflection, rollout=args.rollout, name=args.name))
    text, num_generated_codes = get_tree_text(mcts.root_node)
    print(text)
    print(f"Generated {num_generated_codes} unique codes.")

    with open(f"results/{args.task}_tree{args.name}.txt", "w") as f:
        f.write(f"Generated {num_generated_codes} unique codes.\n")
        f.write(f"Best node: {best_node}, score: {best_node.raw_reward}\n")
        f.write(text)


