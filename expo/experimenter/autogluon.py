from autogluon.tabular import TabularDataset, TabularPredictor

from expo.experimenter.custom import CustomExperimenter


class AGRunner:
    preset = "best_quality"
    time_limit = 500

    def __init__(self, datasets):
        self.datasets = datasets

    def run(self):
        train_path = self.datasets["train"]
        test_wo_target_path = self.datasets["test_wo_target"]
        dev_wo_target_path = self.datasets["dev_wo_target"]
        target_col = self.state["dataset_config"]["target_col"]
        train_data = TabularDataset(train_path)
        test_data = TabularDataset(test_wo_target_path)
        dev_data = TabularDataset(dev_wo_target_path)

        predictor = TabularPredictor(label=target_col).fit(train_data, presets=self.preset, time_limit=self.time_limit)
        test_preds = predictor.predict(test_data)
        dev_preds = predictor.predict(dev_data)
        return {"test_preds": test_preds, "dev_preds": dev_preds}


class GluonExperimenter(CustomExperimenter):
    result_path: str = "results/autogluon"

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.framework = AGRunner(self.datasets)
