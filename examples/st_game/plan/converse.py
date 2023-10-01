#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : conversation between two agents

from typing import Union, Tuple

from metagpt.logs import logger

from ..maze import Maze
from ..roles.st_role import STRole
from ..memory.retrieve import new_retrieve
from ..actions.agent_chat_sum_rel import AgentChatSumRel
from ..actions.gen_iter_chat_utt import GenIterChatUTT


def agent_conversation(maze: Maze, init_role: STRole, target_role: STRole) -> list[str]:
    curr_chat = []
    logger.info(f"Role: {init_role.name} starts a conversation with Role: {target_role.name}")

    conv_rounds = 8
    for idx in range(conv_rounds):
        scratch = init_role._rc.scratch
        target_scratch = target_role._rc.scratch

        focal_points = [f"{target_scratch.name}"]
        retrieved = new_retrieve(init_role, focal_points, 50)
        relationship = generate_summarize_agent_relationship(init_role, target_role, retrieved)
        print("-------- relationship: ", relationship)
        last_chat = ""
        for i in curr_chat[-4:]:
            last_chat += ": ".join(i) + "\n"
        if last_chat:
            focal_points = [f"{relationship}",
                            f"{target_scratch.name} is {target_scratch.act_description}",
                            last_chat]
        else:
            focal_points = [f"{relationship}",
                            f"{target_scratch.name} is {target_scratch.act_description}"]
        retrieved = new_retrieve(init_role, focal_points, 15)
        utt, end = generate_one_utterance(maze, init_role, target_role, retrieved, curr_chat)

        curr_chat += [[scratch.name, utt]]
        if end:
            break

        focal_points = [f"{scratch.name}"]
        retrieved = new_retrieve(target_role, focal_points, 50)
        relationship = generate_summarize_agent_relationship(target_role, init_role, retrieved)
        print("-------- relationship: ", relationship)
        last_chat = ""
        for i in curr_chat[-4:]:
            last_chat += ": ".join(i) + "\n"
        if last_chat:
            focal_points = [f"{relationship}",
                            f"{scratch.name} is {scratch.act_description}",
                            last_chat]
        else:
            focal_points = [f"{relationship}",
                            f"{scratch.name} is {scratch.act_description}"]
        retrieved = new_retrieve(target_role, focal_points, 15)
        utt, end = generate_one_utterance(maze, target_role, init_role, retrieved, curr_chat)

        curr_chat += [[target_scratch.name, utt]]
        if end:
            break

    print("July 23 PU")
    for row in curr_chat:
        print(row)
    print("July 23 FIN")

    return curr_chat


def generate_summarize_agent_relationship(init_role: STRole,
                                          target_role: STRole,
                                          retrieved: dict) -> str:
    all_embedding_keys = list()
    for key, val in retrieved.items():
        for i in val:
            all_embedding_keys += [i.embedding_key]
    all_embedding_key_str = ""
    for i in all_embedding_keys:
        all_embedding_key_str += f"{i}\n"

    summarized_relationship = AgentChatSumRel().run(init_role,
                                                    target_role,
                                                    all_embedding_key_str)
    return summarized_relationship


def generate_one_utterance(maze: Maze, init_role, target_role, retrieved: dict, curr_chat: list) -> Tuple[str, str]:
    # Chat version optimized for speed via batch generation
    scratch = init_role._rc.scratch
    target_scratch = target_role._rc.scratch
    curr_context = (f"{scratch.name} " +
                    f"was {scratch.act_description} " +
                    f"when {scratch.name} " +
                    f"saw {target_scratch.name} " +
                    f"in the middle of {target_scratch.act_description}.\n")
    curr_context += (f"{scratch.name} " +
                     f"is initiating a conversation with " +
                     f"{target_scratch.name}.")

    print("July 23 5")
    x = GenIterChatUTT().run(maze, init_role, target_role, retrieved, curr_context, curr_chat)

    print("July 23 6")

    return x["utterance"], x["end"]
