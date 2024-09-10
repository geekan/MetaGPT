from datetime import datetime
from autogluon.tabular import TabularDataset, TabularPredictor
from expo.experimenter.custom import CustomExperimenter


class AGRunner:
    preset = "best_quality"
    time_limit = 1000 # 1000s

    def __init__(self, state=None):
        self.state = state
        self.datasets = self.state["datasets_dir"]

    def run(self):
        train_path = self.datasets["train"]
        dev_wo_target_path = self.datasets["dev_wo_target"]
        test_wo_target_path = self.datasets["test_wo_target"]
        target_col = self.state["dataset_config"]["target_col"]
        train_data = TabularDataset(train_path)
        dev_data = TabularDataset(dev_wo_target_path)
        test_data = TabularDataset(test_wo_target_path)
        eval_metric = self.state["dataset_config"]["metric"].replace(" ", "_")
        # predictor = TabularPredictor(label=target_col, eval_metric=eval_metric, path="AutogluonModels/ag-{}-{}".format(self.state['task'], datetime.now().strftime("%y%m%d_%H%M"))).fit(train_data, presets=self.preset, time_limit=self.time_limit, fit_weighted_ensemble=False, num_gpus=1)
        predictor = TabularPredictor(label=target_col, eval_metric=eval_metric, path="AutogluonModels/ag-{}-{}".format(self.state['task'], datetime.now().strftime("%y%m%d_%H%M"))).fit(train_data, num_gpus=1)
        dev_preds = predictor.predict(dev_data)
        test_preds = predictor.predict(test_data)
        return {"test_preds": test_preds, "dev_preds": dev_preds}


class GluonExperimenter(CustomExperimenter):
    result_path: str = "results/autogluon"

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.framework = AGRunner(self.state)

    def run_experiment(self):
        result = self.framework.run()
        user_requirement = self.state["requirement"]
        dev_preds = result["dev_preds"]
        test_preds = result["test_preds"]
        score_dict = {
            "dev_score": self.evaluate_predictions(dev_preds, "dev"),
            "test_score": self.evaluate_predictions(test_preds, "test"),
        }
        results = [0, {"score_dict": score_dict, "user_requirement": user_requirement, "args": vars(self.args)}]
        self.save_result(results)
        return results