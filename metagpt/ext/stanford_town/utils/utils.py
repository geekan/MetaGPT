#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : utils

import csv
import errno
import json
import os
import shutil
import time
from pathlib import Path
from typing import Union

from openai import OpenAI

from metagpt.config2 import config
from metagpt.logs import logger


def read_csv_to_list(curr_file: str, header=False, strip_trail=True):
    """
    Reads in a csv file to a list of list. If header is True, it returns a
    tuple with (header row, all rows)
    ARGS:
      curr_file: path to the current csv file.
    RETURNS:
      List of list where the component lists are the rows of the file.
    """
    logger.debug(f"start read csv: {curr_file}")
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
    embedding = None
    if not text:
        text = "this is blank"
    for idx in range(3):
        try:
            embedding = (
                OpenAI(api_key=config.llm.api_key).embeddings.create(input=[text], model=model).data[0].embedding
            )
        except Exception as exp:
            logger.info(f"get_embedding failed, exp: {exp}, will retry.")
            time.sleep(5)
    if not embedding:
        raise ValueError("get_embedding failed")
    return embedding


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


def path_finder_v2(a, start, end, collision_block_char) -> list[int]:
    def make_step(m, k):
        for i in range(len(m)):
            for j in range(len(m[i])):
                if m[i][j] == k:
                    if i > 0 and m[i - 1][j] == 0 and a[i - 1][j] == 0:
                        m[i - 1][j] = k + 1
                    if j > 0 and m[i][j - 1] == 0 and a[i][j - 1] == 0:
                        m[i][j - 1] = k + 1
                    if i < len(m) - 1 and m[i + 1][j] == 0 and a[i + 1][j] == 0:
                        m[i + 1][j] = k + 1
                    if j < len(m[i]) - 1 and m[i][j + 1] == 0 and a[i][j + 1] == 0:
                        m[i][j + 1] = k + 1

    new_maze = []
    for row in a:
        new_row = []
        for j in row:
            if j == collision_block_char:
                new_row += [1]
            else:
                new_row += [0]
        new_maze += [new_row]
    a = new_maze

    m = []
    for i in range(len(a)):
        m.append([])
        for j in range(len(a[i])):
            m[-1].append(0)
    i, j = start
    m[i][j] = 1

    k = 0
    except_handle = 150
    while m[end[0]][end[1]] == 0:
        k += 1
        make_step(m, k)

        if except_handle == 0:
            break
        except_handle -= 1

    i, j = end
    k = m[i][j]
    the_path = [(i, j)]
    while k > 1:
        if i > 0 and m[i - 1][j] == k - 1:
            i, j = i - 1, j
            the_path.append((i, j))
            k -= 1
        elif j > 0 and m[i][j - 1] == k - 1:
            i, j = i, j - 1
            the_path.append((i, j))
            k -= 1
        elif i < len(m) - 1 and m[i + 1][j] == k - 1:
            i, j = i + 1, j
            the_path.append((i, j))
            k -= 1
        elif j < len(m[i]) - 1 and m[i][j + 1] == k - 1:
            i, j = i, j + 1
            the_path.append((i, j))
            k -= 1

    the_path.reverse()
    return the_path


def path_finder(collision_maze: list, start: list[int], end: list[int], collision_block_char: str) -> list[int]:
    # EMERGENCY PATCH
    start = (start[1], start[0])
    end = (end[1], end[0])
    # END EMERGENCY PATCH

    path = path_finder_v2(collision_maze, start, end, collision_block_char)

    new_path = []
    for i in path:
        new_path += [(i[1], i[0])]
    path = new_path

    return path


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
    return [path_to_dir + "/" + filename for filename in filenames if filename.endswith(suffix)]


def copy_folder(src_folder: str, dest_folder: str):
    try:
        if Path(dest_folder).exists():
            logger.warning(f"{dest_folder} exist, start to remove.")
            shutil.rmtree(dest_folder)
        shutil.copytree(src_folder, dest_folder)
    except OSError as exc:  # python >2.5
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src_folder, dest_folder)
        else:
            raise
