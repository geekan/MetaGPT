import shutil

from metagpt.ext.sela.evaluation.evaluation import (
    node_evaluate_score_mlebench,
    node_evaluate_score_sela,
)
from metagpt.ext.sela.evaluation.visualize_mcts import get_tree_text
from metagpt.ext.sela.runner.runner import Runner
from metagpt.ext.sela.search.search_algorithm import MCTS, Greedy, Random


class MCTSRunner(Runner):
    result_path: str = "results/mcts"

    def __init__(self, args, data_config=None, tree_mode=None, **kwargs):
        if args.special_instruction == "image":
            self.start_task_id = 1  # start from datapreprocessing if it is image task
        else:
            self.start_task_id = args.start_task_id

        if args.eval_func == "sela":
            self.eval_func = node_evaluate_score_sela
        elif args.eval_func == "mlebench":
            self.eval_func = node_evaluate_score_mlebench

        super().__init__(args, data_config=data_config, **kwargs)
        self.tree_mode = tree_mode

    async def run_experiment(self):
        use_fixed_insights = self.args.use_fixed_insights
        depth = self.args.max_depth
        if self.tree_mode == "greedy":
            mcts = Greedy(root_node=None, max_depth=depth, use_fixed_insights=use_fixed_insights)
        elif self.tree_mode == "random":
            mcts = Random(root_node=None, max_depth=depth, use_fixed_insights=use_fixed_insights)
        else:
            mcts = MCTS(root_node=None, max_depth=depth, use_fixed_insights=use_fixed_insights)
        best_nodes = await mcts.search(state=self.state, args=self.args, data_config=self.data_config)
        best_node = best_nodes["global_best"]
        dev_best_node = best_nodes["dev_best"]
        score_dict = best_nodes["scores"]
        additional_scores = {"grader": self.eval_func(dev_best_node)}

        text, num_generated_codes = get_tree_text(mcts.root_node)
        text += f"Generated {num_generated_codes} unique codes.\n"
        text += f"Best node: {best_node.id}, score: {best_node.raw_reward}\n"
        text += f"Dev best node: {dev_best_node.id}, score: {dev_best_node.raw_reward}\n"
        text += f"Grader score: {additional_scores['grader']}\n"
        print(text)
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
                "scores": score_dict,
                "additional_scores": additional_scores,
            }
        ]
        self.save_result(results)
        self.copy_notebook(best_node, "best")
        self.copy_notebook(dev_best_node, "dev_best")
        self.save_tree(text)

    def copy_notebook(self, node, name):
        node_dir = node.get_node_dir()
        node_nb_dir = f"{node_dir}/Node-{node.id}.ipynb"
        save_name = self.get_save_name()
        copy_nb_dir = f"{self.result_path}/{save_name}_{name}.ipynb"
        shutil.copy(node_nb_dir, copy_nb_dir)

    def save_tree(self, tree_text):
        save_name = self.get_save_name()
        fpath = f"{self.result_path}/{save_name}_tree.txt"
        with open(fpath, "w") as f:
            f.write(tree_text)
