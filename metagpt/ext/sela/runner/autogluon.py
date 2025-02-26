import os
from datetime import datetime

import pandas as pd

from metagpt.ext.sela.runner.custom import CustomRunner


class AGRunner:
    def __init__(self, state=None):
        self.state = state
        self.datasets = self.state["datasets_dir"]

    def run(self):
        from autogluon.tabular import TabularDataset, TabularPredictor

        train_path = self.datasets["train"]
        dev_path = self.datasets["dev"]
        dev_wo_target_path = self.datasets["dev_wo_target"]
        test_wo_target_path = self.datasets["test_wo_target"]
        target_col = self.state["dataset_config"]["target_col"]
        train_data = TabularDataset(train_path)
        dev_data = TabularDataset(dev_path)
        dev_wo_target_data = TabularDataset(dev_wo_target_path)
        test_data = TabularDataset(test_wo_target_path)
        eval_metric = self.state["dataset_config"]["metric"].replace(" ", "_")
        predictor = TabularPredictor(
            label=target_col,
            eval_metric=eval_metric,
            path="AutogluonModels/ag-{}-{}".format(self.state["task"], datetime.now().strftime("%y%m%d_%H%M")),
        ).fit(train_data=train_data, tuning_data=dev_data, num_gpus=1)
        dev_preds = predictor.predict(dev_wo_target_data)
        test_preds = predictor.predict(test_data)
        return {"test_preds": test_preds, "dev_preds": dev_preds}

    def run_multimodal(self):
        from autogluon.multimodal import MultiModalPredictor

        target_col = self.state["dataset_config"]["target_col"]
        train_path = self.datasets["train"]
        dev_path = self.datasets["dev"]
        dev_wo_target_path = self.datasets["dev_wo_target"]  # Updated variable name
        test_wo_target_path = self.datasets["test_wo_target"]
        eval_metric = self.state["dataset_config"]["metric"].replace(" ", "_")

        # Load the datasets
        train_data, dev_data, dev_wo_target_data, test_data = self.load_split_dataset(
            train_path, dev_path, dev_wo_target_path, test_wo_target_path
        )

        # Create and fit the predictor
        predictor = MultiModalPredictor(
            label=target_col,
            eval_metric=eval_metric,
            path="AutogluonModels/ag-{}-{}".format(self.state["task"], datetime.now().strftime("%y%m%d_%H%M")),
        ).fit(train_data=train_data, tuning_data=dev_data)

        # Make predictions on dev and test datasets
        dev_preds = predictor.predict(dev_wo_target_data)
        test_preds = predictor.predict(test_data)

        # Return predictions for dev and test datasets
        return {"dev_preds": dev_preds, "test_preds": test_preds}

    def load_split_dataset(self, train_path, dev_path, dev_wo_target_path, test_wo_target_path):
        """
        Loads training, dev, and test datasets from given file paths

        Args:
            train_path (str): Path to the training dataset.
            dev_path (str): Path to the dev dataset with target labels.
            dev_wo_target_path (str): Path to the dev dataset without target labels.
            test_wo_target_path (str): Path to the test dataset without target labels.

        Returns:
            train_data (pd.DataFrame): Loaded training dataset with updated image paths.
            dev_data (pd.DataFrame): Loaded dev dataset with updated image paths.
            dev_wo_target_data (pd.DataFrame): Loaded dev dataset without target labels and updated image paths.
            test_data (pd.DataFrame): Loaded test dataset with updated image paths.
        """

        # Define the root path to append
        root_folder = os.path.join("F:/Download/Dataset/", self.state["task"])

        # Load the datasets
        train_data = pd.read_csv(train_path)
        dev_data = pd.read_csv(dev_path)  # Load dev dataset with target labels
        dev_wo_target_data = pd.read_csv(dev_wo_target_path)  # Load dev dataset without target labels
        test_data = pd.read_csv(test_wo_target_path)

        # Get the name of the first column (assuming it's the image path column)
        image_column = train_data.columns[0]

        # Append root folder path to the image column in each dataset
        train_data[image_column] = train_data[image_column].apply(lambda x: os.path.join(root_folder, x))
        dev_data[image_column] = dev_data[image_column].apply(lambda x: os.path.join(root_folder, x))
        dev_wo_target_data[image_column] = dev_wo_target_data[image_column].apply(
            lambda x: os.path.join(root_folder, x)
        )
        test_data[image_column] = test_data[image_column].apply(lambda x: os.path.join(root_folder, x))

        return train_data, dev_data, dev_wo_target_data, test_data


class GluonRunner(CustomRunner):
    result_path: str = "results/autogluon"

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.framework = AGRunner(self.state)
        self.is_multimodal = args.is_multimodal if hasattr(args, "is_multimodal") else False

    async def run_experiment(self):
        if not self.is_multimodal:
            result = self.framework.run()
        else:
            result = self.framework.run_multimodal()

        assert result is not None
        user_requirement = self.state["requirement"]
        dev_preds = result["dev_preds"]
        test_preds = result["test_preds"]
        score_dict = {
            "dev_score": self.evaluate_predictions(dev_preds, "dev"),
            "test_score": self.evaluate_predictions(test_preds, "test"),
        }
        results = [0, {"score_dict": score_dict, "user_requirement": user_requirement, "args": vars(self.args)}]
        self.save_result(results)
