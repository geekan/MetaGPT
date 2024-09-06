from expo.evaluation.visualize_mcts import get_tree_text
from expo.experimenter.experimenter import Experimenter
from expo.MCTS import MCTS


class MCTSExperimenter(Experimenter):
    result_path: str = "results/mcts"

    async def run_experiment(self):
        mcts = MCTS(root_node=None, max_depth=5)
        best_nodes = await mcts.search(
            self.args.task,
            self.data_config,
            low_is_better=self.args.low_is_better,
            load_tree=self.args.load_tree,
            reflection=self.args.reflection,
            rollouts=self.args.rollouts,
            name=self.args.name,
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
