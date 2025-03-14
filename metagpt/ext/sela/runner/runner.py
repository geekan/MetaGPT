import datetime
import json
import os

import numpy as np
import pandas as pd

from metagpt.ext.sela.evaluation.evaluation import evaluate_score
from metagpt.ext.sela.experimenter import Experimenter
from metagpt.ext.sela.search.tree_search import create_initial_state
from metagpt.ext.sela.utils import DATA_CONFIG, save_notebook


class Runner:
    result_path: str = "results/base"
    start_task_id = 1

    def __init__(self, args, data_config=None, **kwargs):
        self.args = args
        self.start_time_raw = datetime.datetime.now()
        self.start_time = self.start_time_raw.strftime("%Y%m%d%H%M")
        self.data_config = data_config if data_config is not None else DATA_CONFIG
        self.state = create_initial_state(
            self.args.task,
            start_task_id=self.start_task_id,
            data_config=self.data_config,
            args=self.args,
        )

    async def run_di(self, di, user_requirement, run_idx):
        max_retries = 3
        num_runs = 1
        run_finished = False
        while num_runs <= max_retries and not run_finished:
            try:
                await di.run(user_requirement)
                score_dict = await di.get_score()
                score_dict = self.evaluate(score_dict, self.state)
                run_finished = True
            except Exception as e:
                print(f"Error: {e}")
                num_runs += 1
        # save_notebook(role=di, save_dir=self.result_path, name=f"{self.args.task}_{self.start_time}_{run_idx}")
        save_name = self.get_save_name()
        save_notebook(role=di, save_dir=self.result_path, name=f"{save_name}_{run_idx}")

        if not run_finished:
            score_dict = {"train_score": -1, "dev_score": -1, "test_score": -1, "score": -1}
        return score_dict

    def summarize_results(self, results):
        dev_scores = [result["score_dict"]["dev_score"] for result in results]
        best_dev_score = (
            max(dev_scores)
            if not self.args.low_is_better
            else min([score for score in dev_scores if score != -1] + [np.inf])
        )
        best_score_idx = dev_scores.index(best_dev_score)

        test_scores = [result["score_dict"]["test_score"] for result in results]
        avg_score = sum(test_scores) / len(test_scores)
        global_best_score = (
            max(test_scores)
            if not self.args.low_is_better
            else min([score for i, score in enumerate(test_scores) if dev_scores[i] != -1] + [np.inf])
        )

        results.insert(
            0,
            {
                "best_dev_score": best_dev_score,
                "best_dev_score_idx": best_score_idx,
                "best_dev_test_score": test_scores[best_score_idx],
                "avg_test_score": avg_score,
                "global_best_test_score": global_best_score,
            },
        )
        return results

    async def run_experiment(self):
        state = self.state
        user_requirement = state["requirement"]
        results = []

        for i in range(self.args.num_experiments):
            di = Experimenter(node_id="0", use_reflection=self.args.reflection, role_timeout=self.args.role_timeout)
            score_dict = await self.run_di(di, user_requirement, run_idx=i)
            results.append(
                {"idx": i, "score_dict": score_dict, "user_requirement": user_requirement, "args": vars(self.args)}
            )
            self.save_result(results)  # save intermediate results
        results = self.summarize_results(results)

        self.save_result(results)

    def evaluate_prediction(self, split, state):
        pred_path = os.path.join(state["work_dir"], state["task"], f"{split}_predictions.csv")
        os.makedirs(state["node_dir"], exist_ok=True)
        pred_node_path = os.path.join(state["node_dir"], f"{self.start_time}-{split}_predictions.csv")
        gt_path = os.path.join(state["datasets_dir"][f"{split}_target"])
        preds = pd.read_csv(pred_path)
        preds = preds[preds.columns.tolist()[-1]]
        preds.to_csv(pred_node_path, index=False)
        gt = pd.read_csv(gt_path)["target"]
        metric = state["dataset_config"]["metric"]
        os.remove(pred_path)
        return evaluate_score(preds, gt, metric)

    def evaluate(self, score_dict, state):
        scores = {
            "dev_score": self.evaluate_prediction("dev", state),
            "test_score": self.evaluate_prediction("test", state),
        }
        score_dict.update(scores)
        return score_dict

    def get_save_name(self):
        return f"{self.args.exp_mode}-{self.args.task}_{self.start_time}"

    def save_result(self, result):
        end_time_raw = datetime.datetime.now()
        end_time = end_time_raw.strftime("%Y%m%d%H%M")
        time_info = {
            "start_time": self.start_time,
            "end_time": end_time,
            "duration (seconds)": (end_time_raw - self.start_time_raw).seconds,
        }
        result = result.copy()
        result.insert(0, time_info)
        save_name = self.get_save_name()
        os.makedirs(self.result_path, exist_ok=True)
        with open(f"{self.result_path}/{save_name}.json", "w") as f:
            json.dump(result, f, indent=4)
