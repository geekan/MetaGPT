# -*- coding: utf-8 -*-
# @Date    : 2024-10-20
# @Author  : MoshiQAQ & didi
# @Desc    : Download and extract dataset files

import os
import tarfile
from typing import Dict

import requests
from tqdm import tqdm

from metagpt.logs import logger


def download_file(url: str, filename: str) -> None:
    """Download a file from the given URL and show progress."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)

    with open(filename, "wb") as file:
        for data in response.iter_content(block_size):
            size = file.write(data)
            progress_bar.update(size)
    progress_bar.close()


def extract_tar_gz(filename: str, extract_path: str) -> None:
    """Extract a tar.gz file to the specified path."""
    with tarfile.open(filename, "r:gz") as tar:
        tar.extractall(path=extract_path)


def process_dataset(url: str, filename: str, extract_path: str) -> None:
    """Download, extract, and clean up a dataset."""
    logger.info(f"Downloading {filename}...")
    download_file(url, filename)

    logger.info(f"Extracting {filename}...")
    extract_tar_gz(filename, extract_path)

    logger.info(f"{filename} download and extraction completed.")

    os.remove(filename)
    logger.info(f"Removed {filename}")


# Define the datasets to be downloaded
# Users can modify this list to choose which datasets to download
datasets_to_download: Dict[str, Dict[str, str]] = {
    "datasets": {
        "url": "https://drive.google.com/uc?export=download&id=1DNoegtZiUhWtvkd2xoIuElmIi4ah7k8e",
        "filename": "aflow_data.tar.gz",
        "extract_path": "metagpt/ext/aflow/data",
    },
    "results": {
        "url": "https://drive.google.com/uc?export=download&id=1Sr5wjgKf3bN8OC7G6cO3ynzJqD4w6_Dv",
        "filename": "result.tar.gz",
        "extract_path": "metagpt/ext/aflow/data/results",
    },
    "initial_rounds": {
        "url": "https://drive.google.com/uc?export=download&id=1UBoW4WBWjX2gs4I_jq3ALdXeLdwDJMdP",
        "filename": "initial_rounds.tar.gz",
        "extract_path": "metagpt/ext/aflow/scripts/optimized",
    },
}


def download(required_datasets, if_first_download: bool = True):
    """Main function to process all selected datasets"""
    if if_first_download:
        for dataset_name in required_datasets:
            dataset = datasets_to_download[dataset_name]
            extract_path = dataset["extract_path"]
            process_dataset(dataset["url"], dataset["filename"], extract_path)
    else:
        logger.info("Skip downloading datasets")
