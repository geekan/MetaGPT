from pathlib import Path

import numpy as np
from datasets import load_dataset, load_from_disk


def extract_patch(command_output):
    patch_lines = []
    recording = False
    for line in command_output.split("\n"):
        if line.startswith("diff --git"):
            recording = True
        if recording:
            patch_lines.append(line)
    return "\n".join(patch_lines)


def load_hf_dataset(dataset_name_or_path: str, cache_dir, split: str = "test", existing_ids: list = []):
    data_dir = cache_dir / dataset_name_or_path
    if Path(data_dir).exists():
        dataset = load_from_disk(data_dir)
    else:
        dataset = load_dataset(dataset_name_or_path)
        dataset.save_to_disk(data_dir)
    print(dataset)
    if split not in dataset:
        raise ValueError(f"Invalid split {split} for dataset {dataset_name_or_path}")
    dataset = dataset[split]
    np.array(list(map(len, dataset["instance_id"])))

    if existing_ids:
        dataset = dataset.filter(
            lambda x: x["instance_id"] not in existing_ids,
            desc="Filtering out existing ids",
            load_from_cache_file=False,
        )

    return dataset
