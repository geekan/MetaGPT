import asyncio
import io
import os
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from PIL import Image

from metagpt.ext.sela.data.dataset import (
    ExpDataset,
    parse_args,
    process_dataset,
    save_datasets_dict_to_yaml,
)
from metagpt.ext.sela.insights.solution_designer import SolutionDesigner
from metagpt.ext.sela.utils import DATA_CONFIG

HFDATSETS = [
    {"name": "sms_spam", "dataset_name": "ucirvine/sms_spam", "target_col": "label", "modality": "text"},
    {"name": "banking77", "dataset_name": "PolyAI/banking77", "target_col": "label", "modality": "text"},
    {"name": "gnad10", "dataset_name": "community-datasets/gnad10", "target_col": "label", "modality": "text"},
    {
        "name": "oxford-iiit-pet",
        "dataset_name": "timm/oxford-iiit-pet",
        "image_col": "image",
        "target_col": "label",
        "modality": "image",
    },
    {
        "name": "stanford_cars",
        "dataset_name": "tanganke/stanford_cars",
        "image_col": "image",
        "target_col": "label",
        "modality": "image",
    },
    {
        "name": "fashion_mnist",
        "dataset_name": "zalando-datasets/fashion_mnist",
        "image_col": "image",
        "target_col": "label",
        "modality": "image",
    },
]


class HFExpDataset(ExpDataset):
    train_ratio = 0.6
    dev_ratio = 0.2
    test_ratio = 0.2

    def __init__(self, name, dataset_dir, dataset_name, **kwargs):
        self.name = name
        self.dataset_dir = dataset_dir
        self.dataset_name = dataset_name
        self.modality = kwargs.get("modality", "")
        self.target_col = kwargs.get("target_col", "label")
        self.image_col = kwargs.get("image_col", "image")
        self.dataset = load_dataset(self.dataset_name, trust_remote_code=True)
        super().__init__(self.name, dataset_dir, **kwargs)

    def get_raw_dataset(self):
        raw_dir = Path(self.dataset_dir, self.name, "raw")
        raw_dir.mkdir(parents=True, exist_ok=True)

        if os.path.exists(Path(raw_dir, "train.csv")):
            df = pd.read_csv(Path(raw_dir, "train.csv"), encoding="utf-8")
        else:
            df = self.dataset["train"].to_pandas()

            if self.modality == "image":
                df = self.save_images_and_update_df(df, raw_dir, "train")

            df.to_csv(Path(raw_dir, "train.csv"), index=False, encoding="utf-8")

        if os.path.exists(Path(raw_dir, "test.csv")):
            test_df = pd.read_csv(Path(raw_dir, "test.csv"), encoding="utf-8")
        else:
            if self.dataset and "test" in self.dataset:
                test_df = self.dataset["test"].to_pandas()

                if self.modality == "image":
                    test_df = self.save_images_and_update_df(test_df, raw_dir, "test")

                test_df.to_csv(Path(raw_dir, "test.csv"), index=False, encoding="utf-8")
            else:
                test_df = None

        return df, test_df

    def save_images_and_update_df(self, df, raw_dir, split):
        abs_image_dir = Path(raw_dir, f"{split}_images")
        rel_image_dir = f"raw/{split}_images"
        abs_image_dir.mkdir(parents=True, exist_ok=True)

        def process_image(idx, row):
            image_bytes = row[self.image_col]["bytes"]
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode == "RGBA":
                image = image.convert("RGB")
            img_path = Path(abs_image_dir, f"{idx}.jpg")
            rel_img_path = f"{rel_image_dir}/{idx}.jpg"
            image.save(img_path)
            return rel_img_path

        df["image"] = df.apply(lambda row: process_image(row.name, row), axis=1)
        return df

    def get_df_head(self, raw_df):
        examples = []
        for i in range(5):
            examples.append(raw_df.iloc[i].to_dict())
        return examples

    def get_dataset_info(self):
        dataset_info = super().get_dataset_info()
        dataset = self.dataset
        dataset_info["description"] = dataset["train"].info.description
        return dataset_info


if __name__ == "__main__":
    dataset_dir = DATA_CONFIG["datasets_dir"]
    args = parse_args()
    force_update = args.force_update
    save_analysis_pool = args.save_analysis_pool
    datasets_dict = {"datasets": {}}
    solution_designer = SolutionDesigner()
    for dataset_meta in HFDATSETS:
        hf_dataset = HFExpDataset(
            dataset_meta["name"],
            dataset_dir,
            dataset_meta["dataset_name"],
            target_col=dataset_meta["target_col"],
            image_col=dataset_meta.get("image_col", ""),
            force_update=force_update,
            modality=dataset_meta["modality"],
        )
        asyncio.run(process_dataset(hf_dataset, solution_designer, save_analysis_pool, datasets_dict))
    save_datasets_dict_to_yaml(datasets_dict, "hf_datasets.yaml")
