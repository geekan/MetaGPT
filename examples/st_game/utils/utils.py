#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : utils

from typing import Any
import json
import openai
from pathlib import Path
import csv


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

def embedding_tools(query):
    embedding_result = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=query
    )
    embedding_key = embedding_result['data'][0]["embedding"]
    return embedding_key

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

