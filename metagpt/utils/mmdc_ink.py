#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/4 10:53
@Author  : alexanderwu, imjohndoe
@File    : mermaid.py
"""

import requests
import base64
import os

import click
@click.command()
@click.version_option()
@click.option("-i","--mermaid_code", type=str, help="mermaid code")
@click.option("-o","--output_file_without_suffix", type=str, help="output filename without suffix")
def mermaid_to_file(mermaid_code, output_file_without_suffix):
    """suffix: png/svg
    :param mermaid_code: mermaid code
    :param output_file_without_suffix: output filename without suffix
    :return: 0 if succeed, -1 if failed
    """
    print('Starting mermaid_to_file command of mermaid.ink...')

    encoded_string = base64.b64encode(mermaid_code.encode()).decode()

    dir_name = os.path.dirname(output_file_without_suffix)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(f"{output_file_without_suffix}.mmd", "w", encoding="utf-8") as f:
        f.write(mermaid_code)

    for suffix in ["svg", "png"]:
        output_file = f"{output_file_without_suffix}.{suffix}"
        path_type = "svg" if suffix == "svg" else "img"
        url = f"https://mermaid.ink/{path_type}/{encoded_string}"
        response = requests.get(url)

        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"Generating {output_file}..")
        else:
            print(f"Failed to retrieve {suffix}")
            return -1

    return 0

if __name__ == "__main__":
    mermaid_to_file()