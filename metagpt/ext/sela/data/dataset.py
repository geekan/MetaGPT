import argparse
import asyncio
import json
import os
from pathlib import Path

import openml
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

from metagpt.ext.sela.insights.solution_designer import SolutionDesigner
from metagpt.ext.sela.utils import DATA_CONFIG

BASE_USER_REQUIREMENT = """
This is a {datasetname} dataset. Your goal is to predict the target column `{target_col}`.
Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. 
Report {metric} on the eval data. Do not plot or make any visualizations.
"""

USE_AG = """
- Please use autogluon for model training with presets='medium_quality', time_limit=None, give dev dataset to tuning_data, and use right eval_metric.
"""

TEXT_MODALITY = """
- You could use models from transformers library for this text dataset.
- Use gpu if available for faster training.
"""

IMAGE_MODALITY = """
- You could use models from transformers/torchvision library for this image dataset.
- Use gpu if available for faster training.
"""

STACKING = """
- To avoid overfitting, train a weighted ensemble model such as StackingClassifier or StackingRegressor.
- You could do some quick model prototyping to see which models work best and then use them in the ensemble. 
"""


SPECIAL_INSTRUCTIONS = {"ag": USE_AG, "stacking": STACKING, "text": TEXT_MODALITY, "image": IMAGE_MODALITY}

DI_INSTRUCTION = """
## Attention
1. Please do not leak the target label in any form during training.
2. Test set does not have the target column.
3. When conducting data exploration or analysis, print out the results of your findings.
4. You should perform transformations on train, dev, and test sets at the same time (it's a good idea to define functions for this and avoid code repetition).
5. When scaling or transforming features, make sure the target column is not included.
6. You could utilize dev set to validate and improve model training. {special_instruction}

## Saving Dev and Test Predictions
1. Save the prediction results of BOTH the dev set and test set in `dev_predictions.csv` and `test_predictions.csv` respectively in the output directory. 
- Both files should contain a single column named `target` with the predicted values.
2. Make sure the prediction results are in the same format as the target column in the original training set. 
- For instance, if the original target column is a list of string, the prediction results should also be strings.

## Output Performance
Print the train and dev set performance in the last step.

# Output dir
{output_dir}
"""

TASK_PROMPT = """
# User requirement
{user_requirement}
{additional_instruction}
# Data dir
train set (with labels): {train_path}
dev set (with labels): {dev_path}
test set (without labels): {test_path}
dataset description: {data_info_path} (During EDA, you can use this file to get additional information about the dataset)
"""


SEED = 100
TRAIN_TEST_SPLIT = 0.8
TRAIN_DEV_SPLIT = 0.75

OPENML_DATASET_IDS = [
    # reg
    41021,
    42727,
    41980,
    42225,
    531,
    # cls
    41143,
    31,
    42733,
    41162,
    1067,
    # multi cls
    40498,
    40982,
    12,
    40984,
    4538,
]

CUSTOM_DATASETS = [
    ("04_titanic", "Survived"),
    ("05_house-prices-advanced-regression-techniques", "SalePrice"),
    ("06_santander-customer-transaction-prediction", "target"),
    ("07_icr-identify-age-related-conditions", "Class"),
]

DSAGENT_DATASETS = [("concrete-strength", "Strength"), ("smoker-status", "smoking"), ("software-defects", "defects")]


def get_split_dataset_path(dataset_name, config):
    datasets_dir = config["datasets_dir"]
    if dataset_name in config["datasets"]:
        dataset = config["datasets"][dataset_name]
        # Check whether `dataset["dataset"]` is already the suffix of `datasets_dir`. If it isn't, perform path concatenation.
        if datasets_dir.rpartition("/")[-1] == dataset["dataset"]:
            data_path = datasets_dir
        else:
            data_path = Path(datasets_dir) / dataset["dataset"]
        split_datasets = {
            "train": os.path.join(data_path, "split_train.csv"),
            "dev": os.path.join(data_path, "split_dev.csv"),
            "dev_wo_target": os.path.join(data_path, "split_dev_wo_target.csv"),
            "dev_target": os.path.join(data_path, "split_dev_target.csv"),
            "test": os.path.join(data_path, "split_test.csv"),
            "test_wo_target": os.path.join(data_path, "split_test_wo_target.csv"),
            "test_target": os.path.join(data_path, "split_test_target.csv"),
        }
        return split_datasets
    else:
        raise ValueError(
            f"Dataset {dataset_name} not found in config file. Available datasets: {config['datasets'].keys()}"
        )


def get_user_requirement(task_name, config):
    # datasets_dir = config["datasets_dir"]
    if task_name in config["datasets"]:
        dataset = config["datasets"][task_name]
        # data_path = os.path.join(datasets_dir, dataset["dataset"])
        user_requirement = dataset["user_requirement"]
        return user_requirement
    else:
        raise ValueError(
            f"Dataset {task_name} not found in config file. Available datasets: {config['datasets'].keys()}"
        )


def save_datasets_dict_to_yaml(datasets_dict, name="datasets.yaml"):
    with open(name, "w") as file:
        yaml.dump(datasets_dict, file)


def create_dataset_dict(dataset):
    dataset_dict = {
        "dataset": dataset.name,
        "user_requirement": dataset.create_base_requirement(),
        "metric": dataset.get_metric(),
        "target_col": dataset.target_col,
    }
    return dataset_dict


def generate_di_instruction(output_dir, special_instruction):
    if special_instruction:
        special_instruction_prompt = SPECIAL_INSTRUCTIONS[special_instruction]
    else:
        special_instruction_prompt = ""
    additional_instruction = DI_INSTRUCTION.format(
        output_dir=output_dir, special_instruction=special_instruction_prompt
    )
    return additional_instruction


def generate_task_requirement(task_name, data_config, is_di=True, special_instruction=None):
    user_requirement = get_user_requirement(task_name, data_config)
    split_dataset_path = get_split_dataset_path(task_name, data_config)
    train_path = split_dataset_path["train"]
    dev_path = split_dataset_path["dev"]
    test_path = split_dataset_path["test_wo_target"]
    work_dir = data_config["work_dir"]
    output_dir = f"{work_dir}/{task_name}"
    datasets_dir = data_config["datasets_dir"]
    data_info_path = f"{datasets_dir}/{task_name}/dataset_info.json"
    if is_di:
        additional_instruction = generate_di_instruction(output_dir, special_instruction)
    else:
        additional_instruction = ""
    user_requirement = TASK_PROMPT.format(
        user_requirement=user_requirement,
        train_path=train_path,
        dev_path=dev_path,
        test_path=test_path,
        additional_instruction=additional_instruction,
        data_info_path=data_info_path,
    )
    print(user_requirement)
    return user_requirement


class ExpDataset:
    description: str = None
    metadata: dict = None
    dataset_dir: str = None
    target_col: str = None
    name: str = None

    def __init__(self, name, dataset_dir, **kwargs):
        self.name = name
        self.dataset_dir = dataset_dir
        self.target_col = kwargs.get("target_col", None)
        self.force_update = kwargs.get("force_update", False)
        self.save_dataset(target_col=self.target_col)

    def check_dataset_exists(self):
        fnames = [
            "split_train.csv",
            "split_dev.csv",
            "split_test.csv",
            "split_dev_wo_target.csv",
            "split_dev_target.csv",
            "split_test_wo_target.csv",
            "split_test_target.csv",
        ]
        for fname in fnames:
            if not os.path.exists(Path(self.dataset_dir, self.name, fname)):
                return False
        return True

    def check_datasetinfo_exists(self):
        return os.path.exists(Path(self.dataset_dir, self.name, "dataset_info.json"))

    def get_raw_dataset(self):
        raw_dir = Path(self.dataset_dir, self.name, "raw")
        train_df = None
        test_df = None
        if not os.path.exists(Path(raw_dir, "train.csv")):
            raise FileNotFoundError(f"Raw dataset `train.csv` not found in {raw_dir}")
        else:
            train_df = pd.read_csv(Path(raw_dir, "train.csv"))
        if os.path.exists(Path(raw_dir, "test.csv")):
            test_df = pd.read_csv(Path(raw_dir, "test.csv"))
        return train_df, test_df

    def get_dataset_info(self):
        raw_df = pd.read_csv(Path(self.dataset_dir, self.name, "raw", "train.csv"))
        metadata = {
            "NumberOfClasses": raw_df[self.target_col].nunique(),
            "NumberOfFeatures": raw_df.shape[1],
            "NumberOfInstances": raw_df.shape[0],
            "NumberOfInstancesWithMissingValues": int(raw_df.isnull().any(axis=1).sum()),
            "NumberOfMissingValues": int(raw_df.isnull().sum().sum()),
            "NumberOfNumericFeatures": raw_df.select_dtypes(include=["number"]).shape[1],
            "NumberOfSymbolicFeatures": raw_df.select_dtypes(include=["object"]).shape[1],
        }

        df_head_text = self.get_df_head(raw_df)

        dataset_info = {
            "name": self.name,
            "description": "",
            "target_col": self.target_col,
            "metadata": metadata,
            "df_head": df_head_text,
        }
        return dataset_info

    def get_df_head(self, raw_df):
        return raw_df.head().to_string(index=False)

    def get_metric(self):
        dataset_info = self.get_dataset_info()
        num_classes = dataset_info["metadata"]["NumberOfClasses"]
        if num_classes == 2:
            metric = "f1 binary"
        elif 2 < num_classes <= 200:
            metric = "f1 weighted"
        elif num_classes > 200 or num_classes == 0:
            metric = "rmse"
        else:
            raise ValueError(f"Number of classes {num_classes} not supported")
        return metric

    def create_base_requirement(self):
        metric = self.get_metric()
        req = BASE_USER_REQUIREMENT.format(datasetname=self.name, target_col=self.target_col, metric=metric)
        return req

    def save_dataset(self, target_col):
        df, test_df = self.get_raw_dataset()
        if not self.check_dataset_exists() or self.force_update:
            print(f"Saving Dataset {self.name} in {self.dataset_dir}")
            self.split_and_save(df, target_col, test_df=test_df)
        else:
            print(f"Dataset {self.name} already exists")
        if not self.check_datasetinfo_exists() or self.force_update:
            print(f"Saving Dataset info for {self.name}")
            dataset_info = self.get_dataset_info()
            self.save_datasetinfo(dataset_info)
        else:
            print(f"Dataset info for {self.name} already exists")

    def save_datasetinfo(self, dataset_info):
        with open(Path(self.dataset_dir, self.name, "dataset_info.json"), "w", encoding="utf-8") as file:
            # utf-8 encoding is required
            json.dump(dataset_info, file, indent=4, ensure_ascii=False)

    def save_split_datasets(self, df, split, target_col=None):
        path = Path(self.dataset_dir, self.name)
        df.to_csv(Path(path, f"split_{split}.csv"), index=False)
        if target_col:
            df_wo_target = df.drop(columns=[target_col])
            df_wo_target.to_csv(Path(path, f"split_{split}_wo_target.csv"), index=False)
            df_target = df[[target_col]].copy()
            if target_col != "target":
                df_target["target"] = df_target[target_col]
                df_target = df_target.drop(columns=[target_col])
            df_target.to_csv(Path(path, f"split_{split}_target.csv"), index=False)

    def split_and_save(self, df, target_col, test_df=None):
        if not target_col:
            raise ValueError("Target column not provided")
        if test_df is None:
            train, test = train_test_split(df, test_size=1 - TRAIN_TEST_SPLIT, random_state=SEED)
        else:
            train = df
            test = test_df
        train, dev = train_test_split(train, test_size=1 - TRAIN_DEV_SPLIT, random_state=SEED)
        self.save_split_datasets(train, "train")
        self.save_split_datasets(dev, "dev", target_col)
        self.save_split_datasets(test, "test", target_col)


class OpenMLExpDataset(ExpDataset):
    def __init__(self, name, dataset_dir, dataset_id, **kwargs):
        self.dataset_id = dataset_id
        self.dataset = openml.datasets.get_dataset(
            self.dataset_id, download_data=False, download_qualities=False, download_features_meta_data=True
        )
        self.name = self.dataset.name
        self.target_col = self.dataset.default_target_attribute
        super().__init__(self.name, dataset_dir, target_col=self.target_col, **kwargs)

    def get_raw_dataset(self):
        dataset = self.dataset
        dataset_df, *_ = dataset.get_data()
        raw_dir = Path(self.dataset_dir, self.name, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        dataset_df.to_csv(Path(raw_dir, "train.csv"), index=False)
        return dataset_df, None

    def get_dataset_info(self):
        dataset_info = super().get_dataset_info()
        dataset = self.dataset
        dataset_info["name"] = dataset.name
        dataset_info["description"] = dataset.description
        dataset_info["metadata"].update(dataset.qualities)
        return dataset_info


async def process_dataset(dataset, solution_designer: SolutionDesigner, save_analysis_pool, datasets_dict):
    if save_analysis_pool:
        await solution_designer.generate_solutions(dataset.get_dataset_info(), dataset.name)
    dataset_dict = create_dataset_dict(dataset)
    datasets_dict["datasets"][dataset.name] = dataset_dict


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force_update", action="store_true", help="Force update datasets")
    parser.add_argument("--save_analysis_pool", action="store_true", help="Save analysis pool")
    parser.add_argument(
        "--no_save_analysis_pool", dest="save_analysis_pool", action="store_false", help="Do not save analysis pool"
    )
    parser.set_defaults(save_analysis_pool=True)
    return parser.parse_args()


if __name__ == "__main__":
    datasets_dir = DATA_CONFIG["datasets_dir"]
    args = parse_args()
    force_update = args.force_update
    save_analysis_pool = args.save_analysis_pool
    datasets_dict = {"datasets": {}}
    solution_designer = SolutionDesigner()
    for dataset_id in OPENML_DATASET_IDS:
        openml_dataset = OpenMLExpDataset("", datasets_dir, dataset_id, force_update=force_update)
        asyncio.run(process_dataset(openml_dataset, solution_designer, save_analysis_pool, datasets_dict))

    for dataset_name, target_col in CUSTOM_DATASETS:
        custom_dataset = ExpDataset(dataset_name, datasets_dir, target_col=target_col, force_update=force_update)
        asyncio.run(process_dataset(custom_dataset, solution_designer, save_analysis_pool, datasets_dict))

    for dataset_name, target_col in DSAGENT_DATASETS:
        custom_dataset = ExpDataset(dataset_name, datasets_dir, target_col=target_col, force_update=force_update)
        asyncio.run(process_dataset(custom_dataset, solution_designer, save_analysis_pool, datasets_dict))

    save_datasets_dict_to_yaml(datasets_dict)
