#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : utils

from typing import Any, Union
import json
import openai
from pathlib import Path
import csv
import os
from ..prompts.run_gpt_prompts import get_poignancy_action, get_poignancy_chat


def read_json_file(json_file: str, encoding=None) -> list[Any]:
    if not Path(json_file).exists():
        raise FileNotFoundError(f"json_file: {json_file} not exist, return []")

    with open(json_file, "r", encoding=encoding) as fin:
        try:
            data = json.load(fin)
        except Exception as exp:
            raise ValueError(f"read json file: {json_file} failed")
    return data


def write_json_file(json_file: str, data: list, encoding=None):
    with open(json_file, "w", encoding=encoding) as fout:
        json.dump(data, fout, ensure_ascii=False, indent=4)


def read_csv_to_list(curr_file: str, header=False, strip_trail=True):
    """
    Reads in a csv file to a list of list. If header is True, it returns a 
    tuple with (header row, all rows)
    ARGS:
      curr_file: path to the current csv file. 
    RETURNS: 
      List of list where the component lists are the rows of the file. 
    """
    if not header:
        analysis_list = []
        with open(curr_file) as f_analysis_file:
            data_reader = csv.reader(f_analysis_file, delimiter=",")
        for count, row in enumerate(data_reader):
            if strip_trail:
                row = [i.strip() for i in row]
            analysis_list += [row]
        return analysis_list
    else:
        analysis_list = []
        with open(curr_file) as f_analysis_file:
            data_reader = csv.reader(f_analysis_file, delimiter=",")
        for count, row in enumerate(data_reader):
            if strip_trail:
                row = [i.strip() for i in row]
            analysis_list += [row]
        return analysis_list[0], analysis_list[1:]


def get_embedding(text, model: str = "text-embedding-ada-002"):
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"
    return openai.Embedding.create(
        input=[text], model=model)['data'][0]['embedding']


def generate_poig_score(scratch, event_type, description):
    if "is idle" in description:
        return 1
    if event_type == "action":
        return get_poignancy_action(scratch, description)[0]
    elif event_type == "chat":
        return get_poignancy_chat(scratch, description)[0]


def extract_first_json_dict(data_str: str) -> Union[None, dict]:
    # Find the first occurrence of a JSON object within the string
    start_idx = data_str.find("{")
    end_idx = data_str.find("}", start_idx) + 1

    # Check if both start and end indices were found
    if start_idx == -1 or end_idx == 0:
        return None

    # Extract the first JSON dictionary
    json_str = data_str[start_idx:end_idx]

    try:
        # Attempt to parse the JSON data
        json_dict = json.loads(json_str)
        return json_dict
    except json.JSONDecodeError:
        # If parsing fails, return None
        return None

def check_if_file_exists(curr_file):
    """
    Checks if a file exists
    ARGS:
        curr_file: path to the current csv file.
    RETURNS:
        True if the file exists
        False if the file does not exist
    """
    try:
        with open(curr_file) as f_analysis_file:
            pass
        return True
    except:
        return False

def create_folder_if_not_there(curr_path):
    """
    Checks if a folder in the curr_path exists. If it does not exist, creates
    the folder.
    Note that if the curr_path designates a file location, it will operate on
    the folder that contains the file. But the function also works even if the
    path designates to just a folder.
    Args:
        curr_list: list to write. The list comes in the following form:
                   [['key1', 'val1-1', 'val1-2'...],
                    ['key2', 'val2-1', 'val2-2'...],]
        outfile: name of the csv file to write
    RETURNS:
        True: if a new folder is created
        False: if a new folder is not created
    """
    outfolder_name = curr_path.split("/")
    if len(outfolder_name) != 1:
        # This checks if the curr path is a file or a folder.
        if "." in outfolder_name[-1]:
            outfolder_name = outfolder_name[:-1]

        outfolder_name = "/".join(outfolder_name)
        if not os.path.exists(outfolder_name):
            os.makedirs(outfolder_name)
            return True

    return False

def find_filenames(path_to_dir, suffix=".csv"):
    """
    Given a directory, find all files that end with the provided suffix and
    return their paths.
    ARGS:
        path_to_dir: Path to the current directory
        suffix: The target suffix.
    RETURNS:
        A list of paths to all files in the directory.
    """
    filenames = os.listdir(path_to_dir)
    return [path_to_dir + "/" + filename
            for filename in filenames if filename.endswith(suffix)]
