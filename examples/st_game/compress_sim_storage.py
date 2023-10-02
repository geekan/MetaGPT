"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: compress_sim_storage.py
Description: Compresses a simulation for replay demos.
"""

import shutil
import json
from utils.utils import find_filenames, create_folder_if_not_there
from utils.const import STORAGE_PATH


def compress(sim_code):
    # 构建文件路径
    sim_storage = str(STORAGE_PATH.joinpath(f"{sim_code}"))
    compressed_storage = str(STORAGE_PATH.joinpath(f"compressed_storage/{sim_code}"))
    persona_folder = sim_storage + "/personas"
    move_folder = sim_storage + "/movement"
    meta_file = sim_storage + "/reverie/meta.json"

    # 收集角色名称
    persona_names = []
    for i in find_filenames(persona_folder, ""):
        x = i.split("/")[-1].strip()
        if x[0] != ".":
            persona_names += [x]

    # 最大移动计算
    max_move_count = max([int(i.split("/")[-1].split(".")[0])
                         for i in find_filenames(move_folder, "json")])

    persona_last_move = dict()
    master_move = dict()
    for i in range(max_move_count + 1):
        master_move[i] = dict()
        with open(f"{move_folder}/{str(i)}.json") as json_file:
            i_move_dict = json.load(json_file)["persona"]
            for p in persona_names:
                move = False
                if i == 0:
                    move = True
                elif (i_move_dict[p]["movement"] != persona_last_move[p]["movement"]
                      or i_move_dict[p]["pronunciatio"] != persona_last_move[p]["pronunciatio"]
                      or i_move_dict[p]["description"] != persona_last_move[p]["description"]
                      or i_move_dict[p]["chat"] != persona_last_move[p]["chat"]):
                    move = True

                if move:
                    persona_last_move[p] = {"movement": i_move_dict[p]["movement"],
                                            "pronunciatio": i_move_dict[p]["pronunciatio"],
                                            "description": i_move_dict[p]["description"],
                                            "chat": i_move_dict[p]["chat"]}
                    master_move[i][p] = {"movement": i_move_dict[p]["movement"],
                                         "pronunciatio": i_move_dict[p]["pronunciatio"],
                                         "description": i_move_dict[p]["description"],
                                         "chat": i_move_dict[p]["chat"]}

    # 创建存储目录
    create_folder_if_not_there(compressed_storage)
    with open(f"{compressed_storage}/master_movement.json", "w") as outfile:
        outfile.write(json.dumps(master_move, indent=2))

    shutil.copyfile(meta_file, f"{compressed_storage}/meta.json")
    shutil.copytree(persona_folder, f"{compressed_storage}/personas/")

if __name__ == '__main__':
    compress("July1_the_ville_isabella_maria_klaus-step-3-9")
