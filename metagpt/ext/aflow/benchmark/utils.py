#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/7/24 16:37
@Author  : didi
@File    : utils.py
"""

import json
import os

import numpy as np

from metagpt.utils.common import read_json_file, write_json_file


def generate_random_indices(n, n_samples, test=False):
    """
    Generate random indices
    """

    def _set_seed(seed=42):
        np.random.seed(seed)

    _set_seed()
    indices = np.arange(n)
    np.random.shuffle(indices)
    if test:
        return indices[n_samples:]
    else:
        return indices[:n_samples]


def split_data_set(file_path, samples, test=False):
    data = []

    with open(file_path, "r") as file:
        for line in file:
            data.append(json.loads(line))
    random_indices = generate_random_indices(len(data), samples, test)
    data = [data[i] for i in random_indices]
    return data


def log_mismatch(problem, expected_output, prediction, predicted_number, path):
    log_data = {
        "question": problem,
        "right_answer": expected_output,
        "model_output": prediction,
        "extracted_output": predicted_number,
    }

    log_file = os.path.join(path, "log.json")

    # Check if the log file already exists
    if os.path.exists(log_file):
        # If it exists, load the existing log data
        data = read_json_file(log_file)
    else:
        # If it does not exist, create a new log list
        data = []

    # Add the new log entry
    data.append(log_data)

    # Write the data back to log.json file
    write_json_file(log_file, data, encoding="utf-8", indent=4)
