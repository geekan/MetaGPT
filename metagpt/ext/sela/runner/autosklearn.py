from datetime import datetime
from functools import partial

import pandas as pd

from metagpt.ext.sela.evaluation.evaluation import evaluate_score
from metagpt.ext.sela.runner.custom import CustomRunner


def custom_scorer(y_true, y_pred, metric_name):
    return evaluate_score(y_pred, y_true, metric_name)


class ASRunner:
    time_limit = 600

    def __init__(self, state=None):
        self.state = state
        self.datasets = self.state["datasets_dir"]

    def create_autosklearn_scorer(self, metric_name):
        from autosklearn.metrics import make_scorer

        return make_scorer(name=metric_name, score_func=partial(custom_scorer, metric_name=metric_name))

    def run(self):
        import autosklearn.classification
        import autosklearn.regression

        train_path = self.datasets["train"]
        dev_wo_target_path = self.datasets["dev_wo_target"]
        test_wo_target_path = self.datasets["test_wo_target"]
        target_col = self.state["dataset_config"]["target_col"]

        train_data = pd.read_csv(train_path)
        dev_data = pd.read_csv(dev_wo_target_path)
        test_data = pd.read_csv(test_wo_target_path)
        eval_metric = self.state["dataset_config"]["metric"]
        X_train = train_data.drop(columns=[target_col])
        y_train = train_data[target_col]

        if eval_metric == "rmse":
            automl = autosklearn.regression.AutoSklearnRegressor(
                time_left_for_this_task=self.time_limit,
                metric=self.create_autosklearn_scorer(eval_metric),
                memory_limit=8192,
                tmp_folder="AutosklearnModels/as-{}-{}".format(
                    self.state["task"], datetime.now().strftime("%y%m%d_%H%M")
                ),
                n_jobs=-1,
            )
        elif eval_metric in ["f1", "f1 weighted"]:
            automl = autosklearn.classification.AutoSklearnClassifier(
                time_left_for_this_task=self.time_limit,
                metric=self.create_autosklearn_scorer(eval_metric),
                memory_limit=8192,
                tmp_folder="AutosklearnModels/as-{}-{}".format(
                    self.state["task"], datetime.now().strftime("%y%m%d_%H%M")
                ),
                n_jobs=-1,
            )
        else:
            raise ValueError(f"Unsupported metric: {eval_metric}")
        automl.fit(X_train, y_train)

        dev_preds = automl.predict(dev_data)
        test_preds = automl.predict(test_data)

        return {"test_preds": test_preds, "dev_preds": dev_preds}


class AutoSklearnRunner(CustomRunner):
    result_path: str = "results/autosklearn"

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.framework = ASRunner(self.state)

    async def run_experiment(self):
        result = self.framework.run()
        user_requirement = self.state["requirement"]
        dev_preds = result["dev_preds"]
        test_preds = result["test_preds"]
        score_dict = {
            "dev_score": self.evaluate_predictions(dev_preds, "dev"),
            "test_score": self.evaluate_predictions(test_preds, "test"),
        }
        results = [
            0,
            {
                "score_dict": score_dict,
                "user_requirement": user_requirement,
                "args": vars(self.args),
            },
        ]
        self.save_result(results)
