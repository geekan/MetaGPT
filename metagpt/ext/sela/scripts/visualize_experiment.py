import networkx as nx

from metagpt.ext.sela.evaluation.visualize_mcts import (
    build_tree_recursive,
    visualize_tree,
)
from metagpt.ext.sela.MCTS import MCTS, create_initial_state, initialize_di_root_node
from metagpt.ext.sela.run_experiment import get_args
from metagpt.ext.sela.utils import DATA_CONFIG

if __name__ == "__main__":
    args = get_args()
    data_config = DATA_CONFIG
    state = create_initial_state(args.task, 0, data_config, args=args)
    role, node = initialize_di_root_node(state)
    mcts = MCTS(
        root_node=node,
        max_depth=5,
        use_fixed_insights=False,
    )

    mcts.load_tree()
    mcts.load_node_order()
    root = mcts.root_node
    node_order = mcts.node_order
    G = nx.DiGraph()
    build_tree_recursive(G, "0", root, node_order)
    visualize_tree(G, save_path=f"results/{args.task}-tree.png")
