from expo.evaluation.visualize_mcts import get_tree_text
from expo.experimenter.experimenter import Experimenter
from expo.Greedy import Greedy, Random
from expo.MCTS import MCTS


class MCTSExperimenter(Experimenter):
    result_path: str = "results/mcts"
    start_task_id = 2

    def __init__(self, args, tree_mode=None, **kwargs):
        super().__init__(args, **kwargs)
        self.tree_mode = tree_mode

    async def run_experiment(self):
        if self.tree_mode == "greedy":
            mcts = Greedy(root_node=None, max_depth=5, use_fixed_insights=self.args.use_fixed_insights)
        elif self.tree_mode == "random":
            mcts = Random(root_node=None, max_depth=5, use_fixed_insights=self.args.use_fixed_insights)
        else:
            mcts = MCTS(root_node=None, max_depth=5, use_fixed_insights=self.args.use_fixed_insights)
        best_nodes = await mcts.search(
            state=self.state,
            reflection=self.args.reflection,
            rollouts=self.args.rollouts,
            load_tree=self.args.load_tree,
        )
        best_node = best_nodes["global_best"]
        dev_best_node = best_nodes["dev_best"]

        text, num_generated_codes = get_tree_text(mcts.root_node)
        text += f"Generated {num_generated_codes} unique codes.\n"
        text += f"Best node: {best_node.id}, score: {best_node.raw_reward}\n"
        text += f"Dev best node: {dev_best_node.id}, score: {dev_best_node.raw_reward}\n"
        print(text)
        self.save_tree(text)

        results = [
            {
                "best_node": best_node.id,
                "best_node_score": best_node.raw_reward,
                "dev_best_node": dev_best_node.id,
                "dev_best_node_score": dev_best_node.raw_reward,
                "num_generated_codes": num_generated_codes,
                "user_requirement": best_node.state["requirement"],
                "tree_text": text,
                "args": vars(self.args),
            }
        ]
        self.save_result(results)

    def save_tree(self, tree_text):
        fpath = f"{self.result_path}/{self.args.task}_tree_{self.args.name}.txt"
        with open(fpath, "w") as f:
            f.write(tree_text)
