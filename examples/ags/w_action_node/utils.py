# -*- coding: utf-8 -*-
# @Date    : 7/2/2024 17:36 PM
# @Author  : didi
# @Desc    : utils for experiment

import json
import re
from typing import List, Dict, Any

def extract_task_id(task_id: str) -> int:
    """Extract the numeric part of the task_id."""
    match = re.search(r'/(\d+)', task_id)
    return int(match.group(1)) if match else 0

def jsonl_ranker(input_file: str, output_file: str):
    """
    Read a JSONL file, sort the entries based on task_id, and write to a new JSONL file.
    
    :param input_file: Path to the input JSONL file
    :param output_file: Path to the output JSONL file
    """
    # Read and parse the JSONL file
    with open(input_file, 'r') as f:
        data = [json.loads(line) for line in f]
    
    # Sort the data based on the numeric part of task_id
    sorted_data = sorted(data, key=lambda x: extract_task_id(x['task_id']))
    
    # Write the sorted data to a new JSONL file
    with open(output_file, 'w') as f:
        for item in sorted_data:
            f.write(json.dumps(item) + '\n')