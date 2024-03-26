# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from pathlib import Path

import numpy as np
from datasets import load_dataset, load_from_disk

from benchmark.swe_bench.inference.const import SCIKIT_LEARN_IDS


def load_oracle_dataset(dataset_name_or_path: str = "", split: str = "test", existing_ids: list = []):
    if Path(dataset_name_or_path).exists():
        dataset = load_from_disk(dataset_name_or_path)
    else:
        dataset = load_dataset(dataset_name_or_path)
    if split not in dataset:
        raise ValueError(f"Invalid split {split} for dataset {dataset_name_or_path}")
    dataset = dataset[split]
    lens = np.array(list(map(len, dataset["text"])))
    dataset = dataset.select(np.argsort(lens))

    if len(existing_ids) > 0:
        dataset = dataset.filter(
            lambda x: x["instance_id"] not in existing_ids,
            desc="Filtering out existing ids",
            load_from_cache_file=False,
        )
    if len(SCIKIT_LEARN_IDS) > 0:
        dataset = dataset.filter(
            lambda x: x["instance_id"] in SCIKIT_LEARN_IDS,
            desc="Filtering out subset_instance_ids",
            load_from_cache_file=False,
        )
    return dataset
