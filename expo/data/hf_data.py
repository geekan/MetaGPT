import asyncio
import os
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from expo.data.dataset import ExpDataset, process_dataset, save_datasets_dict_to_yaml
from expo.insights.solution_designer import SolutionDesigner

HFDATSETS = [
    {"name": "sms_spam", "dataset_name": "ucirvine/sms_spam", "target_col": "label"},
    {"name": "banking77", "dataset_name": "PolyAI/banking77", "target_col": "label"},
    {"name": "gnad10", "dataset_name": "community-datasets/gnad10", "target_col": "label"},
    {"name": "oxford-iiit-pet", "dataset_name": "timm/oxford-iiit-pet", "target_col": "label"},
    {"name": "stanford_cars", "dataset_name": "tanganke/stanford_cars", "target_col": "label"},
    {"name": "fashion_mnist", "dataset_name": "zalando-datasets/fashion_mnist", "target_col": "label"},
]


class HFExpDataset(ExpDataset):
    train_ratio = 0.6
    dev_ratio = 0.2
    test_ratio = 0.2

    def __init__(self, name, dataset_dir, dataset_name, **kwargs):
        self.name = name
        self.dataset_dir = dataset_dir
        self.dataset_name = dataset_name
        self.target_col = kwargs.get("target_col", "label")
        self.dataset = load_dataset(dataset_name)
        super().__init__(self.name, dataset_dir, **kwargs)

    def get_raw_dataset(self):
        raw_dir = Path(self.dataset_dir, self.name, "raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        if os.path.exists(Path(raw_dir, "train.csv")):
            df = pd.read_csv(Path(raw_dir, "train.csv"))
        else:
            df = self.dataset["train"].to_pandas()
            df.to_csv(Path(raw_dir, "train.csv"), index=False)

        if os.path.exists(Path(raw_dir, "test.csv")):
            test_df = pd.read_csv(Path(raw_dir, "test.csv"), index=False)
        else:
            if "test" in self.dataset:
                test_df = self.dataset["test"].to_pandas()
                test_df.to_csv(Path(raw_dir, "test.csv"), index=False)
            else:
                test_df = None
        return df, test_df

    # def get_df_head(self, raw_df):
    #     return raw_df.head()


if __name__ == "__main__":
    dataset_dir = "D:/work/automl/datasets"
    save_analysis_pool = True
    datasets_dict = {"datasets": {}}
    solution_designer = SolutionDesigner()
    for dataset_meta in HFDATSETS:
        hf_dataset = HFExpDataset(
            dataset_meta["name"], dataset_dir, dataset_meta["dataset_name"], target_col=dataset_meta["target_col"]
        )
        asyncio.run(process_dataset(hf_dataset, solution_designer, save_analysis_pool, datasets_dict))
    save_datasets_dict_to_yaml(datasets_dict, "hf_datasets.yaml")
