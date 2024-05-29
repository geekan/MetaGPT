#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/05/22
@Author  : mannaandpoem
@File    : swe_agent_utils.py
"""
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import load_dataset, load_from_disk
from github import Github

from metagpt.logs import logger

OUTPUT_DIR = Path(__file__).parent
ENV_INFO_DATA = json.load(open(OUTPUT_DIR / "swe_lite_test_env_info.json", "r", encoding="utf-8"))


def extract_repo_identifier(requirement: str) -> str:
    """Extract the repository identifier from requirement."""
    match = re.search(r"github\.com/([^/]+/[^/]+)/issues/\d+", requirement)
    if match:
        return match.group(1)
    return ""


def get_github_issue_description(owner: str, repo_name: str, issue_number: int) -> str:
    """Get the description of a GitHub issue."""
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo(f"{owner}/{repo_name}")
    return repo.get_issue(number=issue_number).body


def filter_and_get_repo_info(
    dataset: pd.DataFrame, filter_column: str, result_dir: str = "", selected_ids: list[str] = None
) -> tuple[pd.DataFrame, dict]:
    """Filter the dataset based on selected and finished IDs and get repository information.

    Args:
        dataset (pd.DataFrame): The dataset to filter.
        filter_column (str): The column name to filter by.
        result_dir (str, optional): The directory containing the results. Defaults to "".
        selected_ids (list[str], optional): List of IDs to include. Defaults to None.

    Returns:
        tuple[pd.DataFrame, dict]: A tuple containing the filtered dataset and a dictionary of repository information.
    """
    # 开始时，subset 是整个数据集
    subset = dataset.copy()

    # 如果all_preds.jsonl存在，则从中获取已完成的任务ID
    # check_existing_ids
    finished_ids = check_existing_ids(f"{result_dir}/all_preds.jsonl")

    subset = subset[~subset[filter_column].isin(finished_ids)]

    # 如果提供了 selected_ids，则只保留这些ID
    if selected_ids:
        subset = subset[subset[filter_column].isin(selected_ids)]

    # 打印筛选后的任务数量
    logger.info(f"Retained {subset.shape[0]} tasks after filtering")

    # Initialize an empty dictionary to store the repository information
    repo_info = {}

    # Iterate over the selected IDs to extract information for each instance
    for _, instance in subset.iterrows():
        instance_id = instance["instance_id"]
        base_commit = instance["base_commit"]
        issue_description = instance["problem_statement"]
        hints_text = instance["hints_text"]
        repo = instance["repo"]

        # ENV_INFO_DATA differs from env_name, it should be two __ separated strings
        # env_name = ENV_INFO_DATA.get(instance_id, "")
        # if not env_name:
        repo_prefix = repo.replace("/", "__")
        version = instance["version"]
        env_name = f"{repo_prefix}__{version}"

        # Record the information of the repository for the current instance ID
        repo_info[instance_id] = {
            "exit_status": "n/a",
            "base_commit": base_commit,
            "issue_description": issue_description,
            "hints_text": hints_text,
            "repo": repo,
            "env_name": env_name,
            "submission": "",
        }

    return subset, repo_info


def get_conda_base_path(python_executable_path):
    # 使用正则表达式匹配 'envs' 前的部分
    envs_marker = os.sep.join(["", "envs", ""])
    envs_index = python_executable_path.find(envs_marker)
    # 如果找到 'envs'
    if envs_index != -1:
        # 返回包含 'envs' 的路径，即截取到 'envs' 之后的第一个路径分隔符
        return python_executable_path[: envs_index + len(envs_marker) - 1]
    else:
        # 如果路径中没有 'envs'，返回 Python 解释器所在的根目录
        return os.path.dirname(os.path.dirname(python_executable_path))


def check_existing_ids(output_file):
    existing_ids = set()
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            for line in f:
                data = json.loads(line)
                instance_id = data["instance_id"]
                existing_ids.add(instance_id)
    return existing_ids


def load_oracle_dataset(
    dataset_name_or_path: str = "", split: str = "test", existing_ids: list = [], selected_id: str = ""
):
    if Path(dataset_name_or_path).exists():
        dataset = load_from_disk(dataset_name_or_path)
    else:
        dataset = load_dataset(dataset_name_or_path)
    if split not in dataset:
        raise ValueError(f"Invalid split {split} for dataset {dataset_name_or_path}")
    dataset = dataset[split]
    lens = np.array(list(map(len, dataset["text"])))
    dataset = dataset.select(np.argsort(lens))

    if existing_ids:
        dataset = dataset.filter(
            lambda x: x["instance_id"] not in existing_ids,
            desc="Filtering out existing ids",
            load_from_cache_file=False,
        )
    if selected_id:
        dataset = dataset.filter(
            lambda x: x["instance_id"] in selected_id,
            desc="Filtering out subset_instance_ids",
            load_from_cache_file=False,
        )
    return dataset
